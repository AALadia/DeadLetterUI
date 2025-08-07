from Settings import *
from mongoDb import testDb
import pytest

db = testDb


def test_settings():
    try:
        #delete all settings
        db.delete({}, collectionNameOfSettings)
        #create default settings
        DatabaseSettingUpdater().updateDatabaseSettingsToDefault()
        #get all settings
        allDatabaseSettings = db.read({}, collectionNameOfSettings)
        allAppSettings = DefaultSettings().getSettings()
        #compare all settings
        assert len(allDatabaseSettings) == len(allAppSettings)
        #get fragileCheckEnabled setting
        settingOld = db.read({"_id": "fragileCheckEnabled"},
                             collectionNameOfSettings,
                             findOne=True)
        # switch setting
        DatabaseSettingUpdater().switchSetting("fragileCheckEnabled")
        # get setting from database
        settingNew = db.read({"_id": "fragileCheckEnabled"},
                             collectionNameOfSettings,
                             findOne=True)
        assert settingOld["value"] != settingNew["value"]
        # delete one database setting
        db.delete({"_id": "qualityCheckEnabled"}, collectionNameOfSettings)
        # check if setting is deleted
        settingDeleted = db.read({"_id": "qualityCheckEnabled"},
                                 collectionNameOfSettings,
                                 findOne=True)
        assert settingDeleted is None
        # create default settings again
        DatabaseSettingUpdater().updateDatabaseSettingsToDefault()
        # get all settings
        allDatabaseSettings = db.read({}, collectionNameOfSettings)
        allAppSettings = DefaultSettings().getSettings()
        # compare all settings
        assert len(allDatabaseSettings) == len(allAppSettings)
        fragileCheckEnabled = db.read({"_id": "fragileCheckEnabled"},
                                      collectionNameOfSettings,
                                      findOne=True)
        assert fragileCheckEnabled["value"] == True
        qualityCheckEnabled = db.read({"_id": "qualityCheckEnabled"},
                                      collectionNameOfSettings,
                                      findOne=True)
        assert qualityCheckEnabled["value"] == False

        fragileCheckEnabled = SettingsGetter().getSettingValue(
            "fragileCheckEnabled")
        assert fragileCheckEnabled == True

        with pytest.raises(Exception):
            SettingsGetter().getSettingValue("nonExistingSetting")

    finally:
        db.delete({}, 'Settings')


if __name__ == "__main__":
    test_settings()
