import Production_IDs_Dict

# get production ids from user
def get_ids():
    ids = {}

    while True:
        k = ''
        v = ''

        # get the key
        k = input("\nEnter numerical ID: ").strip()
        if k == 'q':
            break

        custom_val = False
        try:
            # if the key that the user provided exists in the list of known ids, ask if the user wants to use that key-value pair
            v = Production_IDs_Dict.prod_ids[k]
            print(f"I found a match:\t '{k}': '{v}'")
            ans = input("Would you like to use this match? ")
            if not ans.lower().startswith('y'):
                custom_val = True
        except:
            # if the key that the user provided is unknown, ask if they would like to use it anyway
            # (they would just need to provide their own value)
            ans = input("I don't know your ID, but it might still be valid. Do you want to continue with your ID? ")
            if not ans.lower().startswith('y'):
                continue
            custom_val = True

        # get custom value from user, if needed
        if custom_val:
            v = input("Enter the name you would like to use: ")

        # add key-value pair to list (note that if the key was already provided by the user, the previous one will be overwritten)
        ids[k] = v

        # option to add more key-value pairs
        if not input("Would you like to add more ids? ").lower().startswith('y'):
            break
    
    return ids