"""User Views tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User,Likes,Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test Views for Messages"""

    def setUp(self):
        """create test client, add sample data"""

        db.drop_all()
        db.create_all()

        self.client=app.test_client()

        self.testuser=User.signup(username="testuser",
                                  email="test@testing.com",
                                  password="test",
                                  image_url=None)
        self.testuser_id=9090
        self.testuser.id=self.testuser_id

        self.u1=User.signup("abc","test1@test.com","password",None)
        self.u1_id=111
        self.u1.id=self.u1_id
        self.u2=User.signup("def","test2@test.com","password",None)
        self.u2_id=222
        self.u2.id=self.u2_id
        self.u3=User.signup("aaa","test3@test.com","password",None)
        self.u4=User.signup("TESTING","test4@test.com","password",None)

        db.session.commit()

    def tearDown(self):
        response=super().tearDown()
        db.session.rollback()
        return response
    

    def test_users_index(self):
        with self.client as c:
            response=c.get("/users")

            self.assertIn("@testuser",str(response.data))
            self.assertIn("@abc",str(response.data))
            self.assertIn("@def",str(response.data))
            self.assertIn("@aaa",str(response.data))
            self.assertIn("@TESTING",str(response,data))


    def test_users_search(self):
        with self.client as c:
            response=c.get("/users?q=test")

            self.assertIn("@testuser",str(response.data))
            self.assertIn("@TESTING",str(response.data))
            
            self.assertNotIn("@abc",str(response.data))
            self.assertNotIn("@def",str(response.data))
            self.assertNotIn("@aaa",str(response.data))


    def test_users_show(self):
        with self.client as c:

            response=c.get(f"/users/{self.testuser_id}")

            self.assertEqual(response.status_code,200)

            self.assertIn("@testuser",str(response.data))


    def setup_likes(self):
        m1=Message(text="blahblahblah",user_id=self.testuser_id)
        m2=Message(text="hmmm break time",user_id=self.testuser_id)
        m3=Message(id=4444,text="ugh",user_id=ui_id)

        db.session.add_all([m1,m2,m3])
        db.session.commit()

        likes=Likes(user_id=self.testuser_id,message_id=4444)

        db.session.add(likes)
        db.session.commit()



    def test_add_like(self):
        m = Message(id=1984, text="The earth is round", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/messages/1984/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)


    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="ugh").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==m.id
        ).one()

        # Now we are sure that testuser likes the message "likable warble"
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            response = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            self.assertIn("Access unauthorized", str(response.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    
    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            response = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(response.status_code, 200)
            self.assertIn("@abc", str(response.data))
            self.assertIn("@efg", str(response.data))
            self.assertNotIn("@hij", str(response.data))
            self.assertNotIn("@testing", str(response.data))

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            response = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@abc", str(response.data))
            self.assertNotIn("@efg", str(response.data))
            self.assertNotIn("@hij", str(response.data))
            self.assertNotIn("@testing", str(response.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            response = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("@abc", str(response.data))
            self.assertIn("Access unauthorized", str(response.data))


    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            response = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("@abc", str(response.data))
            self.assertIn("Access unauthorized", str(response.data))
