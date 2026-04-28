def add_task(tasks, title):
    max = 0#if list is empty, max will stay 0
    if tasks:#list not empty
        max = tasks[-1]["id"]#last one's id
    task = {"id": max+1, "title": title, "done": False}
    tasks.append(task)
    return task

def mark_as_done(tasks, id):
    for task in tasks:
        if task["id"] == id:
            task["done"] = True
            return True
    return False

def delete_task(tasks, id):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)#pop only takes index
            return True
    return False

def print_summary(tasks):
    print("Total: ", end=" ")
    for i, task in enumerate(tasks, start = 1):
        print(str(i) + ") " + str(task["id"]) + ", " + task["title"], end=" ")
    print("\n")

    print("Done: ", end= " ")
    for i, task in enumerate(tasks, start = 1):
        if task["done"]:
            print(str(i) + ") " + str(task["id"]) + ", " + task["title"], end=" ")
    print("\n")

    print("Not Done: ", end= " ")
    for i, task in enumerate(tasks, start = 1):
        if task["done"]:
            continue
        print(str(i) + ") " + str(task["id"]) + ", " + task["title"], end=" ")
    print("\n")