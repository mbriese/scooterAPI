"""Quick script to list all users from MongoDB"""
from models.database import init_mongodb, get_users_collection

if __name__ == "__main__":
    print("\n" + "="*50)
    print("       REGISTERED USERS IN MONGODB")
    print("="*50)
    
    if init_mongodb():
        users = list(get_users_collection().find({}, {'password_hash': 0, '_id': 0}))
        
        if users:
            for i, user in enumerate(users, 1):
                print(f"\n[User {i}]")
                print(f"  Name:    {user.get('name', 'N/A')}")
                print(f"  Email:   {user.get('email', 'N/A')}")
                print(f"  Role:    {user.get('role', 'N/A')}")
                print(f"  Active:  {user.get('is_active', 'N/A')}")
                print(f"  Created: {user.get('created_at', 'N/A')}")
            
            print("\n" + "-"*50)
            print(f"Total: {len(users)} user(s)")
        else:
            print("\nNo users found in database.")
    else:
        print("\nFailed to connect to MongoDB!")
    
    print("="*50 + "\n")

