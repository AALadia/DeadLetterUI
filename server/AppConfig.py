import os
import datetime


class Project:
    def __init__(self):
        self.projectName = 'deadLetterUi'
        self.projectId = os.getenv('GOOGLE_CLOUD_PROJECT_ID')

    def getProjectId(self):
        return self.projectId


class MongoDb(Project):
    def __init__(self):
        super().__init__()
        self.databaseName = os.getenv('databaseName') if os.getenv(
            'databaseName') else 'test' + self.projectName

    def getDatabaseName(self):
        return self.databaseName


class Timezone:
    def __init__(self):
        super().__init__()
        #gmt + 8
        self.timezone = 8

    def getTimezone(self):
        return datetime.timezone(datetime.timedelta(hours=self.timezone))


class Environment:
    def __init__(self):
        super().__init__()
        self.environment = os.getenv('ENVIRONMENT')
        if self.environment not in [
                'localdev', 'localprod', 'clouddev', 'cloudprod'
        ]:
            raise Exception("Invalid environment")

       

    def getEnvironment(self):
        return self.environment

    def getIsCloudEnvironment(self):
        return self.getEnvironment() in ['clouddev', 'cloudprod']

    def getIsProductionEnvironment(self):
        return self.getEnvironment() in ['cloudprod']

    def getisLocalDevEnvironment(self):
        return self.getEnvironment() in ['localdev']

    def getisLocalEnvironment(self):
        return self.getEnvironment() in ['localdev', 'localprod']

    def getIsDevEnvironment(self):
        return self.getEnvironment() in ['localdev', 'clouddev']




 


class AppConfig(Environment, Timezone, MongoDb):

    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    appConfig = AppConfig()
