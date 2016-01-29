from celery import shared_task

@shared_task
def test(param):
    return 'Test task with arg: {}'.format(param)
