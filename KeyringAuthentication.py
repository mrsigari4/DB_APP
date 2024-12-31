import keyring

def LoginSetter(username, password):
    us=username
    ps=password
    existing_password = keyring.get_password('DBAPP', us)
    
    if existing_password is not None:
        if existing_password == ps:
            print(f'Login {us} already exists with the same password. No changes made.')
        else:
            keyring.set_password('DBAPP', us, ps)
            print(f'Credentials for user {us} have been updated.')
    else:
        keyring.set_password('DBAPP', us, ps)
        print(f'Credentials for user {us} have been saved.')

def LoginGetter(username):
    us=username
    ps=keyring.get_password('DBAPP', us)
    
    if ps:
        print(f'Password retrieved for user {us}')
        return ps
    else:
        print(f"No credentials found for user {us}.")
        return None