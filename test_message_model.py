"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows,Likes

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
    """Test Message model"""

    def setup(self):
        """create test client,add sample data"""
        db.drop_all()
        db.create_all()

        self.uid=12345
        u=User.signup("testing","testing@test.com","password",None)
        u.id=self.uid
        db.session.commit()

        self.u=User.query.get(self.uid)
        self.client=app.test_client()


    def tearDown(self):
        response=super().tearDown()
        db.session.rollback()
        return response

    def test_message_model(self):
        """does Message Model work?"""

        m=Message(
           
            text="TEST MESSAGE",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        #Message should say "TEST MESSAGE" and have an  len of 1
     

        self.assertEqual(len(self.u.messages,1))
        self.assertEqual(self.u.messages[0].text,"TEST MESSAGE")

    def test_message_likes(self):
        message1=Message(
            text="a message",
            user_id=self.uid
            
        )
        message2=Message(
            text="a silly message",
            user_id=self.uid
        )

        u=User.signup("AGAINTEST","t@test.com","password",None)
        uid=1010
        u.id=uid
      
        db.session.add_all([message1,message2,u])
        db.session.commit()

        u.likes.append(message1)

        db.session.commit()

        l=Likes.query.filter(l.user_id==uid).all()
        self.assertEqual(len(l),1) # check 
        self.assertEqual(l[0].message_id, message1.id)