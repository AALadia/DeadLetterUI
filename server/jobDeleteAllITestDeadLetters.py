from mongoDb import db

def delete_all_test_dead_letters():
    db.delete({'originalMessage.isTestForAppDoNotDelete':True},'DeadLetters')
    # try:
    db.delete({'originalMessage.customer':'test1'},'DeadLetters')
    db.delete({'originalMessage.customer':'test2'},'DeadLetters')
    # except:
    #     pass


if __name__ == '__main__':
    delete_all_test_dead_letters()