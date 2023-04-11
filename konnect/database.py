from os.path import join
from sqlite3 import OperationalError, connect

# This script creates a sql database and provides an interface to manipulate this database. 

class Database:

  # The schema provides the querries to set up the structure. Three tables are created.
  SCHEMA = [
    [
      "CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)", # Config table
      "CREATE TABLE trusted_devices (identifier TEXT PRIMARY KEY, certificate TEXT, name TEXT, type TEXT)", # Trusted devices table
      "CREATE TABLE notifications (reference TEXT, identifier TEXT, [text] TEXT, " # Notifications table
      "title TEXT, application TEXT, PRIMARY KEY (identifier, reference), "
      "FOREIGN KEY (identifier) REFERENCES trusted_devices (identifier) ON DELETE CASCADE)",
      "CREATE INDEX notification_identifier ON notifications (identifier)",
     ],
    [
      "ALTER TABLE notifications ADD COLUMN cancel INTEGER DEFAULT 0"
    ]
  ]

  def __init__(self, path):
    # create and or connect to sqlite3 database at 'path/konnect.db'
    self.instance = connect(join(path, "konnect.db"), isolation_level=None, check_same_thread=False)
    self._upgradeSchema()

  # if the database isn't setup yet, this will iterate through the SCHEMA var 
  # and execute the sql commands listed to setup the database. 
  def _upgradeSchema(self):

    # version trackes the state of the database. The loadConfig loads the state 
    # of the database into the version variable. If the database isn't setup yet 
    # it will default to -1 which in turn unlocks the setuü following.
    version = int(self.loadConfig("schema", -1))

    # Executes the SCHEMA querries and updates the database state version
    for index, queries in enumerate(self.SCHEMA):
      if index > version:
        version = index

        for query in queries:
          self.instance.execute(query)
    # saves the state of the database within the db so the setup prior 
    # will only be executet the first time.
    self.saveConfig("schema", version)

    # this function returns a value from the config sql table by providing 
    # it the a existing key. Optional, if you give a second value this will 
    # function as the "not available" and will be returned if the given key cannot be found.
  def loadConfig(self, key, default=None):
    try:
      query = "SELECT value FROM config WHERE key = ?"
      return self.instance.execute(query, (key,)).fetchone()[0]
    except (OperationalError, TypeError):
      return default

  # This Function saves a value to the config sql table by providing it a key and a value.
  def saveConfig(self, key, value):
    query = "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
    self.instance.execute(query, (key, value))


# This section is dedicated to the manipulation of the trusted devices table.

  # Returns boolean from the trusted devices sql table given a existing identifier.
  def isDeviceTrusted(self, identifier):
    query = "SELECT COUNT(1) FROM trusted_devices WHERE identifier = ?"
    return int(self.instance.execute(query, (identifier,)).fetchone()[0]) == 1

  # Returns a list of all trusted devices saved in the trusted devices sql table
  def getTrustedDevices(self):
    query = "SELECT identifier, name, type FROM trusted_devices"
    return self.instance.execute(query).fetchall()

  # Update the name and type of a device, that is specified by the identifier, 
  # in the trusted devices sql table
  def updateDevice(self, identifier, name, device):
    query = "UPDATE trusted_devices SET name = ?, type = ? WHERE identifier = ?"
    self.instance.execute(query, (name, device, identifier))

  # Add device to the trusted devices table. 
  def pairDevice(self, identifier, certificate, name, device):
    query = "INSERT INTO trusted_devices (identifier, certificate, name, type) VALUES (?, ?, ?, ?)"
    self.instance.execute(query, (identifier, certificate, name, device))

  # Remove device from trusted devices table by their identifier
  def unpairDevice(self, identifier):
    query = "DELETE FROM trusted_devices WHERE identifier = ?"
    self.instance.execute(query, (identifier))


# This section is dedicated to the manipulation of the notifications table.

  # Stores a notification in the notification table, if the identifier and the reference
  # already exist, it will update the existing entry instead of creating a new one.
  def persistNotification(self, identifier, text, title, application, reference):
    query = "INSERT INTO notifications (identifier, [text], title, application, reference) VALUES (?, ?, ?, ?, ?)" \
      "ON CONFLICT(identifier, reference) DO UPDATE SET text = excluded.text, title = excluded.title, application = excluded.application"
    self.instance.execute(query, (identifier, text, title, application, reference))

  # Removes a notification from the notification table.
  def dismissNotification(self, identifier, reference):
    query = "DELETE FROM notifications WHERE identifier = ? AND reference = ?"
    self.instance.execute(query, (identifier, reference))

  # Set a notification to chancel
  def cancelNotification(self, identifier, reference):
    query = "UPDATE notifications SET cancel = ? WHERE identifier = ? AND reference = ?"
    self.instance.execute(query, (1, identifier, reference))

  # Reutrns a notification from the table given the identifier
  def showNotifications(self, identifier):
    query = "SELECT cancel, reference, [text], title, application FROM notifications WHERE identifier = ?"
    return self.instance.execute(query, (identifier,)).fetchall()
