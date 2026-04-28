from storage import load_tasks, save_tasks
from logic import add_task, mark_as_done, delete_task, print_summary

tasks = load_tasks()
choice = 0
while choice != 5:
    print("\n-----MENU:-----\n1-Add task\n2-List tasks\n3-Mark done\n4-Delete task\n5-Exit")
    try:
        choice = int(input("Choose: "))
    except ValueError:
        print("Enter a number.")
        continue
    print("\n")
    
    if choice == 1:
        title = input("Title for the task to be added: ")
        add_task(tasks, title)
        print("Task added.")

    elif choice == 2:
        print_summary(tasks)

    elif choice == 3:
        id = int(input("Id of the task to be marked done: "))
        if mark_as_done(tasks, id):
            print("Task with id " + str(id) + " is marked done.")
        else:
            print("No task with given id.")

    elif choice == 4:
        id = int(input("Id of the task to be deleted: "))
        if delete_task(tasks, id):
            print("Task with id " + str(id) + " is deleted.")
            save_tasks(tasks)#updated
        else:
            print("No task with the given id.")
    elif choice == 5:
        print("Exited menu, saved tasks, bye!")
        save_tasks(tasks)
        break
    else:
        print("Invalid choice, choose one of:1,2,3,4,5")

