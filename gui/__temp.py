completed = 0
finish = False
import time

account_completed = 0
list_acc = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12','13', '14', '15', '16']
def worker(id, complete):
    print(id, 'start')
    complete()

for acc in list_acc:
    def complete():
        global completed
        global account_completed
        completed += 1
        account_completed = len(list_acc) - completed
        if account_completed % 2 == 0:
            print('done')
            time.sleep(3)
    worker(acc, complete)
