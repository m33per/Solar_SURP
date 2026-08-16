import Production_IDs_Dict

# get production ids from user
def get_ids(runMe=False):
    ids = {}

    while runMe:
        k = ''
        v = ''

        # get the key
        k = input("\nEnter numerical ID: ").strip()
        if k == 'q':
            break

        # get the value
        v = input("Enter the name you would like to use: ")

        # add key-value pair to list (note that if the key was already provided by the user, the previous one will be overwritten)
        ids[k] = v

        # option to add more key-value pairs
        if not input("Would you like to add more ids? ").lower().startswith('y'):
            break
    
    return ids