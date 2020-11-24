class ManageUserModel:

    def __init__(self, database):
        self.database = database

    def load_user(self, name):
        self.database.execute(f"select name, passwd, role, access from user where name = '{name}'")
        info_list = self.database.fetchone()
        info = {
            'name': info_list[0],
            'passwd': info_list[1],
            'role': info_list[2],
            'access': info_list[3],
        }
        return info

    def save_user(self, info):
        name = info['name']
        if not self.database.check_user_exist(name):
            self.database.create_user(**info)
        else:
            self.database.update_user(**info)

    def remove_user(self, name):
        self.database.remove_user(name)