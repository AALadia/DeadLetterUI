# settings_service.py
from pymongo.collection import Collection
from pydantic import BaseModel, field_validator, Field, model_validator
from typing import Union, List, Optional
from mongoDb import db

collectionNameOfSettings = 'Settings'
class Setting(BaseModel):
    id : str = Field(..., alias="_id")
    value : bool = Field(..., description="The default value of the setting, True or False")
    description : str | None  = Field(..., description="Description of the setting")
    version : int = Field(default=1,alias="_version")

    def switchValue(self):
        """
        Switch the value of the setting.
        """
        self.value = not self.value

class DefaultSettings():
    def __init__(self):
        self.settings = [
            Setting(_id="fragileCheckEnabled", value=False, description="Require fragile check when second verifying"),
            Setting(_id="qualityCheckEnabled", value=False, description="Require quality check when second verifying"),
        ]

    def getSettings(self) -> List[Setting]:
        """
        Get all default settings.
        """
        return self.settings

    def getSettingById(self, settingId: str) -> Optional[Setting]:
        """
        Get a setting by its ID.
        """
        for setting in self.settings:
            if setting.id == settingId:
                return setting
        return None

class DatabaseSettingUpdater():
    def __init__(self):
        pass

    def switchSetting(self,settingId:str):
        """
        Switch the value of the setting in the database.
        """
        # get setting from database
        setting = db.read({"_id":settingId},collectionNameOfSettings,findOne=True)
        if setting == None:
            raise ValueError('setting id not found')
        setting = Setting(**setting)
        setting.switchValue()
        return db.update({"_id":setting.id,'_version':setting.version}, setting.model_dump(by_alias=True), collectionNameOfSettings)

    def updateDatabaseSettingsToDefault(self):
        """
        Updates the database settings with the default settings if they do not already exist.
        """
        # get all app settings
        allSettings = DefaultSettings().getSettings()
        # get settings in database
        allSettingsInDatabase = db.read({},collectionNameOfSettings)
        allSettingsInDatabaseIds = [setting.get("_id") for setting in allSettingsInDatabase]
        # check if setting already exists
        for setting in allSettings:
            if setting.id not in allSettingsInDatabaseIds:
                db.create(setting.model_dump(by_alias=True), collectionNameOfSettings)
                print(f"Setting {setting.id} created in database")
            else:
                print(f"Setting {setting.id} already exists in database")
            
            
class SettingsGetter:
    def getSetting(self, settingId: str) -> Setting:
        """
        Get a setting from the database by its ID.
        """
        data = db.read({"_id": settingId}, collectionNameOfSettings, findOne=True)
        if data == None:
            setting = DefaultSettings().getSettingById(settingId)
            if setting == None:
                raise Exception(f"Setting {settingId} not found in database or default settings")
            else:
                return setting
        else:
            return Setting(**data)

    def getSettingValue(self, settingId: str) -> bool:
        """
        Get the value of a setting from the database by its ID.
        """
        return self.getSetting(settingId).value

        

if __name__ == "__main__":
    # Test the SettingsGetter class
    DatabaseSettingUpdater().updateDatabaseSettingsToDefault()
    