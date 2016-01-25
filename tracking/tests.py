from django.test import TestCase
from .models import User, Drawing, Revision, Comment, Reply

class ReplyAutoIncrementTestCase(TestCase):
    def setUp(self):
        user = User(username='tester')
        user.save()
        dwg = Drawing(name='TestDrawing')
        dwg.save()
        rev = Revision(number='A', drawing=dwg)
        rev.save()
        com = Comment(desc='unitest', text='unitest text',
                      owner=user)
        com.save()
        com.revision.add(rev)
        com.save()

    def test_reply_auto_increment(self):
        user = User.objects.get(username='tester')
        com = Comment.objects.first()
        newrep = Reply(desc = 'test reply', text='thisis reply text',
                       comment=com, owner=user)
        newrep.save()
        self.assertEqual(newrep.number, 1)
        newrep2 = Reply(desc = 'test reply2', text='thisis reply text2',
               comment=com, owner=user)
        newrep.save()
        self.assertEqual(newrep2.number, 2)
