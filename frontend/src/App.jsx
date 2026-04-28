import { useEffect, useMemo, useState } from "react";
import { apiFetch, clearToken, getToken, saveToken } from "./api";
import "./App.css";
import knightLogo from "./assets/knight.png";

function normalizeSuggestions(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function normalizeText(value) {
  return String(value || "").trim();
}

function normalizeKey(value) {
  return normalizeText(value).toLowerCase();
}

function formatLabel(value) {
  return normalizeText(value).replaceAll("_", " ");
}

function uniqueByCaseInsensitive(items = []) {
  const map = new Map();

  for (const raw of items || []) {
    const value = typeof raw === "string" ? raw : raw?.name;
    const clean = normalizeText(value);
    if (!clean) continue;

    const key = normalizeKey(clean);
    const existing = map.get(key);

    // Prefer the lowercase database value when it exists, because your seed data uses lowercase.
    if (!existing || clean === key) {
      map.set(key, clean);
    }
  }

  return Array.from(map.values()).sort((a, b) => a.localeCompare(b));
}

function preferenceIncludes(list = [], value) {
  const target = normalizeKey(value);
  return (list || []).some((item) => normalizeKey(item) === target);
}

function togglePreferenceValue(list = [], value) {
  const target = normalizeKey(value);
  const filtered = (list || []).filter((item) => normalizeKey(item) !== target);

  if (filtered.length === (list || []).length) {
    filtered.push(value);
  }

  return filtered;
}

function getQuestCategories(quest) {
  return quest?.categories || [];
}

function TagList({ items }) {
  const labels = uniqueByCaseInsensitive((items || []).map((item) => (typeof item === "string" ? item : item?.name)));
  if (labels.length === 0) return <span className="muted">No tags</span>;

  return (
    <div className="tags">
      {labels.map((label) => (
        <span className="tag" key={label}>{formatLabel(label)}</span>
      ))}
    </div>
  );
}

function QuestMeta({ quest }) {
  const parts = [
    formatLabel(quest.location_type),
    formatLabel(quest.cost_level),
    `${formatLabel(quest.social_type)} social`,
    `${formatLabel(quest.effort_level)} effort`,
    `${formatLabel(quest.duration_level)} duration`,
  ].filter(Boolean);

  return <p className="meta">{parts.join(" • ")}</p>;
}

function App() {
  const [token, setToken] = useState(getToken());
  const isLoggedIn = useMemo(() => Boolean(token), [token]);

  const [theme, setTheme] = useState(localStorage.getItem("sidequest-theme") || "green");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [suggestions, setSuggestions] = useState([]);
  const [myQuests, setMyQuests] = useState([]);
  const [options, setOptions] = useState(null);
  const [preferences, setPreferences] = useState(null);

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const cleanedOptions = useMemo(() => {
    if (!options) return null;
    return {
      ...options,
      categories: uniqueByCaseInsensitive(options.categories),
      seasons: uniqueByCaseInsensitive(options.seasons),
      times_of_day: uniqueByCaseInsensitive(options.times_of_day),
    };
  }, [options]);

  useEffect(() => {
    localStorage.setItem("sidequest-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(() => setMessage(""), 3500);
    return () => window.clearTimeout(timer);
  }, [message]);

  function showMessage(text) {
    setMessage(text);
  }

  function handleInvalidToken() {
    clearToken();
    setToken("");
    setMyQuests([]);
    setPreferences(null);
    setSuggestions([]);
    showMessage("Session expired. Please log in again.");
  }

  function handleApiError(err) {
    if (err.message && err.message.toLowerCase().includes("invalid token")) {
      handleInvalidToken();
      return;
    }

    showMessage(err.message);
  }

  async function loadOptions() {
    const opts = await apiFetch("/options/");
    setOptions(opts);
  }

  async function loadUserData(currentToken = token) {
    if (!currentToken) return;

    const [mine, prefs, sugg] = await Promise.all([
      apiFetch("/my-quests/", { token: currentToken }),
      apiFetch("/preferences/", { token: currentToken }),
      apiFetch("/suggestions/?limit=20", { token: currentToken }),
    ]);

    setMyQuests(mine || []);
    setPreferences(prefs || null);
    setSuggestions(normalizeSuggestions(sugg));
  }

  async function loadSurpriseSuggestions() {
    if (!token) return;
    setLoading(true);
    setMessage("");

    try {
      const sugg = await apiFetch("/suggestions/?limit=20&seed=random", { token });
      setSuggestions(normalizeSuggestions(sugg));
      showMessage("Here is a fresh set of suggestions.");
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOptions().catch((err) => handleApiError(err));
  }, []);

  useEffect(() => {
    if (token) {
      loadUserData(token).catch((err) => handleApiError(err));
    } else {
      setMyQuests([]);
      setPreferences(null);
      setSuggestions([]);
    }
  }, [token]);

  async function handleAuth(path, successMessage) {
    setLoading(true);
    setMessage("");

    try {
      const data = await apiFetch(path, {
        method: "POST",
        body: { username, password },
      });

      saveToken(data.token);
      setToken(data.token);
      setPassword("");
      showMessage(successMessage);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    setLoading(true);
    setMessage("");

    try {
      if (token) await apiFetch("/auth/logout/", { method: "POST", token });
    } catch {
      // Clear local token even if it was already invalid on the server.
    } finally {
      clearToken();
      setToken("");
      showMessage("Logged out.");
      setLoading(false);
    }
  }

  async function saveQuest(sidequestId) {
    if (!token) {
      showMessage("Please log in first.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await apiFetch("/my-quests/", {
        method: "POST",
        token,
        body: { sidequest_id: sidequestId },
      });

      showMessage("Quest saved.");
      await loadUserData(token);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  async function toggleDone(userQuest) {
    if (!token) return;

    setLoading(true);
    setMessage("");

    try {
      await apiFetch(`/my-quests/${userQuest.id}/`, {
        method: "PATCH",
        token,
        body: { done: !userQuest.done },
      });

      await loadUserData(token);
      showMessage(userQuest.done ? "Quest moved back to not done." : "Quest marked done.");
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  async function deleteQuest(userQuestId) {
    if (!token) return;

    setLoading(true);
    setMessage("");

    try {
      await apiFetch(`/my-quests/${userQuestId}/`, {
        method: "DELETE",
        token,
      });

      showMessage("Quest removed.");
      await loadUserData(token);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  }

  async function updatePreference(partial, successMessage = "Preferences updated.") {
    if (!token) return false;

    setLoading(true);
    setMessage("");

    try {
      const updated = await apiFetch("/preferences/", {
        method: "PATCH",
        token,
        body: partial,
      });

      setPreferences(updated);
      const sugg = await apiFetch("/suggestions/?limit=20", { token });
      setSuggestions(normalizeSuggestions(sugg));
      showMessage(successMessage);
      return true;
    } catch (err) {
      handleApiError(err);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function resetPreferences() {
    await updatePreference(
      {
        location_type: null,
        social_type: null,
        cost_level: null,
        effort_level: null,
        duration_level: null,
        categories: [],
        seasons: [],
        times_of_day: [],
      },
      "Preferences reset."
    );
  }

  function togglePreferenceList(field, value) {
    const next = togglePreferenceValue(preferences?.[field] || [], value);
    updatePreference({ [field]: next });
  }

  const savedSidequestIds = new Set(myQuests.map((uq) => uq.sidequest?.id));

  return (
    <main className={`page theme-${theme}`}>
      <section className="hero">
        <div>
          <p className="eyebrow">Add color to the mundane</p>
          <div className="brand">
            <h1>SideQuest</h1>
            <img src={knightLogo} alt="Knight errant silhouette" className="brand-icon" />
          </div>
          <p className="subtitle">
            Find and save side quest ideas, track the ones you do, and get suggestions that match your preferences.
          </p>
        </div>

        <div className="theme-switcher" aria-label="Color theme selector">
          <span>Theme</span>
          <div className="theme-buttons">
            <button
              className={theme === "green" ? "theme-button active" : "theme-button"}
              onClick={() => setTheme("green")}
              type="button"
            >
              Green
            </button>
            <button
              className={theme === "pink" ? "theme-button active" : "theme-button"}
              onClick={() => setTheme("pink")}
              type="button"
            >
              Pink
            </button>
          </div>
        </div>
      </section>

      {message && (
        <div className="toast" role="status" aria-live="polite">
          <span>{message}</span>
          <button className="toast-close" onClick={() => setMessage("")} type="button" aria-label="Dismiss message">
            ×
          </button>
        </div>
      )}

      <section className="panel auth-panel">
        <div>
          <h2>{isLoggedIn ? "Account" : "Login / Register"}</h2>
          <p className="muted">
            {isLoggedIn ? "You are logged in." : "Create an account or log in to start using SideQuest."}
          </p>
        </div>

        {!isLoggedIn ? (
          <div className="auth-form">
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
            <button disabled={loading} onClick={() => handleAuth("/auth/register/", "Registered and logged in.")}>Register</button>
            <button disabled={loading} onClick={() => handleAuth("/auth/login/", "Logged in.")}>Login</button>
          </div>
        ) : (
          <button className="secondary" disabled={loading} onClick={handleLogout}>Logout</button>
        )}
      </section>

      {!isLoggedIn && (
        <section className="panel locked-panel">
          <h2>Log in to unlock your quest list</h2>
          <p className="muted">
            After logging in, you can set preferences, get personalized suggestions, save side quests, and mark them done.
          </p>
        </section>
      )}

      {isLoggedIn && cleanedOptions && preferences && (
        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Preferences</h2>
              <p className="muted">Leave a field empty if you do not care about it.</p>
            </div>
            <button
              className="secondary"
              disabled={loading}
              onClick={resetPreferences}
              type="button"
            >
              Reset preferences
            </button>
          </div>

          <div className="preference-grid">
            <label>
              Location
              <select value={preferences.location_type || ""} onChange={(e) => updatePreference({ location_type: e.target.value || null })}>
                <option value="">No preference</option>
                {(cleanedOptions.preference_location_types || cleanedOptions.location_types || []).map((item) => (
                  <option key={item} value={item}>{formatLabel(item)}</option>
                ))}
              </select>
            </label>

            <label>
              Social
              <select value={preferences.social_type || ""} onChange={(e) => updatePreference({ social_type: e.target.value || null })}>
                <option value="">No preference</option>
                {(cleanedOptions.preference_social_types || cleanedOptions.social_types || []).map((item) => (
                  <option key={item} value={item}>{formatLabel(item)}</option>
                ))}
              </select>
            </label>

            <label>
              Cost
              <select value={preferences.cost_level || ""} onChange={(e) => updatePreference({ cost_level: e.target.value || null })}>
                <option value="">No preference</option>
                {cleanedOptions.cost_levels?.map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
              </select>
            </label>

            <label>
              Effort
              <select value={preferences.effort_level || ""} onChange={(e) => updatePreference({ effort_level: e.target.value || null })}>
                <option value="">No preference</option>
                {cleanedOptions.effort_levels?.map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
              </select>
            </label>

            <label>
              Duration
              <select value={preferences.duration_level || ""} onChange={(e) => updatePreference({ duration_level: e.target.value || null })}>
                <option value="">No preference</option>
                {cleanedOptions.duration_levels?.map((item) => <option key={item} value={item}>{formatLabel(item)}</option>)}
              </select>
            </label>
          </div>

          <div className="preference-tags">
            <h3>Categories</h3>
            <div className="chip-row">
              {cleanedOptions.categories?.map((name) => (
                <button
                  key={name}
                  className={preferenceIncludes(preferences.categories, name) ? "chip active" : "chip"}
                  onClick={() => togglePreferenceList("categories", name)}
                  type="button"
                >
                  {formatLabel(name)}
                </button>
              ))}
            </div>
          </div>

          <div className="preference-tags">
            <h3>Seasons</h3>
            <div className="chip-row">
              {cleanedOptions.seasons?.map((name) => (
                <button
                  key={name}
                  className={preferenceIncludes(preferences.seasons, name) ? "chip active" : "chip"}
                  onClick={() => togglePreferenceList("seasons", name)}
                  type="button"
                >
                  {formatLabel(name)}
                </button>
              ))}
            </div>
          </div>

          <div className="preference-tags">
            <h3>Times of day</h3>
            <div className="chip-row">
              {cleanedOptions.times_of_day?.map((name) => (
                <button
                  key={name}
                  className={preferenceIncludes(preferences.times_of_day, name) ? "chip active" : "chip"}
                  onClick={() => togglePreferenceList("times_of_day", name)}
                  type="button"
                >
                  {formatLabel(name)}
                </button>
              ))}
            </div>
          </div>
        </section>
      )}

      {isLoggedIn && (
        <section className="two-column">
          <div className="panel">
            <div className="section-heading">
              <div>
                <h2>Suggestions</h2>
                <p className="muted">Suggested quests you have not saved yet.</p>
              </div>
              <div className="actions">
                <button className="secondary" disabled={loading} onClick={() => loadUserData(token)}>Refresh</button>
                <button className="secondary" disabled={loading} onClick={loadSurpriseSuggestions}>Surprise me</button>
              </div>
            </div>

            <div className="quest-list">
              {suggestions.length === 0 ? (
                <p className="empty">No suggestions right now. Add more catalog items or delete a saved quest.</p>
              ) : suggestions.map((quest) => (
                <article className="quest-card" key={quest.id}>
                  <div>
                    <h3>{quest.title}</h3>
                    <QuestMeta quest={quest} />
                    <TagList items={getQuestCategories(quest)} />
                  </div>
                  <button disabled={loading || savedSidequestIds.has(quest.id)} onClick={() => saveQuest(quest.id)}>
                    {savedSidequestIds.has(quest.id) ? "Saved" : "Save"}
                  </button>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="section-heading">
              <div>
                <h2>My Quests</h2>
                <p className="muted">Your saved side quests.</p>
              </div>
            </div>

            {myQuests.length === 0 ? (
              <p className="empty">No saved quests yet.</p>
            ) : (
              <div className="quest-list">
                {myQuests.map((item) => (
                  <article className="quest-card compact" key={item.id}>
                    <div>
                      <h3>{item.sidequest?.title || "Quest"}</h3>
                      {item.sidequest && <QuestMeta quest={item.sidequest} />}
                      <p className="meta">{item.done ? "Completed" : "Not done yet"}</p>
                    </div>
                    <div className="actions">
                      <button className="secondary" disabled={loading} onClick={() => toggleDone(item)}>{item.done ? "Undo" : "Done"}</button>
                      <button className="danger" disabled={loading} onClick={() => deleteQuest(item.id)}>Delete</button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      )}
      {!isLoggedIn && <p className="credit">By Ayşegül</p>}
    </main>
  );
}

export default App;
