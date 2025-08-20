from mongoDb import db

def delete_all_test_dead_letters():
    db.delete({'originalMessage.isTestForAppDoNotDelete':True},'DeadLetters')

if __name__ == '__main__':
    delete_all_test_dead_letters()