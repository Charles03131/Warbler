"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        TESTUser=User.signup("Test1","test@email.com","password",None)
        TESTUser_id=11
        TESTUser.id=TESTUser_id

        SECONDUser=User.signup("Test2","test@test.com","password",None)
        SECONDUser_id=2
        SECONDUser.id=SECONDUser_id

        db.session.commit()

        TESTUser=User.query.get_or_404(TESTUser_id)
        SECONDUser=User.query.get_or_404(SECONDUser_id)
        self.TESTUser = TESTUser
        self.TESTUser_id = TESTUser_id

        self.SECONDUser = SECONDUser
        self.SECONDUser_id = SECONDUser_id

        self.client = app.test_client()


    def tearDown(self):
        response=super().tearDown()
        db.session.rollback()
        return response

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="testing@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    # TEST FOLLOWING 


    def test_user_follows(self):
        self.TESTUser.following.append(self.SECONDUser)
        db.session.commit()

        self.assertEqual(len(self.SECONDUser.following), 0)
        self.assertEqual(len(self.SECONDUser.followers), 1)
        self.assertEqual(len(self.TESTUser.followers), 0)
        self.assertEqual(len(self.TESTUser.following), 1)

        self.assertEqual(self.SECONDUser.followers[0].id, self.TESTUser.id)
        self.assertEqual(self.TESTUser.following[0].id, self.SECONDUser.id)
    

    def test_is_following(self):
        self.TESTUser.following.append(self.SECONDUser)
        db.session.commit()

        self.assertTrue(self.TESTUser.is_following(self.SECONDUser))
        self.assertFalse(self.SECONDUser.is_following(self.TESTUser))

    def test_is_followed_by(self):
        self.TESTUser.following.append(self.SECONDUser)
        db.session.commit()

        self.assertTrue(self.SECONDUser.is_followed_by(self.TESTUser))
        self.assertFalse(self.TESTUser.is_followed_by(self.SECONDUser))


# SIGNUP TESTS########################################################################

    def test_valid_signup(self):
        user_signup=User.signup("TEST","test5@test.com","password",None)
        userid=23
        user_signup.id=userid
        db.session.commit()

        user_signup=User.query.get(userid)

        self.assertIsNotNone(user_signup)
        self.assertEqual(user_signup.username,"TEST")
        self.assertEqual(user_signup.email,"test5@test.com")
        self.assertNotEqual(user_signup.password,"password")
        
        self.assertTrue(user_signup.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid=User.signup(None,"test@test.com","password",None)
        userid=123456789
        invalid.id=userid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid=User.signup("test",None,"password",None)
        userid=1234567
        invalid.id=userid
        with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest","emial@email.com",None,None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest","email@email.com","",None)


#AUTHENTICATION TESTS#################

    def test_valid_authentication(self):
        user_auth=User.authenticate(self.TESTUser.username,"password")
        self.assertIsNotNone(user_auth)
        self.assertEqual(user_auth.id,self.TESTUser_id) #check this _ instead of .


    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername","password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.TESTUser.username,"badpassword"))
