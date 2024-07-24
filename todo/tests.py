from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task
from django.utils.timezone import make_aware
from django.urls import reverse


# Create your tests here.
class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title='task2')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1')
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_post(self):
        client = Client()
        data = {'title': 'Test Task', 'due_at': '2024-06-30 23:59:59'}
        response = client.post('/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context["tasks"]), 1)

    def test_index_get_order_post(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=post')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=due')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)

    def test_detail_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def test_detail_get_fail(self):
        client = Client()
        response = client.get('/1/')

        self.assertEqual(response.status_code, 404)

    def test_close(self):
        task = Task(title='task', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.post('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="Sample Task",
            due_at=make_aware(datetime.now())
        )

    def test_update(self):
        new_title = "Updated Task"
        new_due_at = make_aware(datetime(2023, 12, 31, 23, 59))

        response = self.client.post(
            reverse('update', args=[self.task.id]),
            data={
                'title': new_title,
                'due_at': new_due_at.isoformat(),
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('detail', args=[self.task.id]))

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, new_title)
        self.assertEqual(self.task.due_at, new_due_at)

class TodoViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.url_index = reverse('index')
        self.url_detail = reverse('detail', args=[1])  

    def test_index_get(self):
        response = self.client.get(self.url_index)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_post(self):
        response = self.client.post(self.url_index, {
            'title': 'New Task',
            'due_at': '2023-12-31T23:59:00',
        })
        self.assertEqual(response.status_code, 200)
        tasks = Task.objects.all()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, 'New Task')

    def test_index_get_order_due(self):
        task1 = Task.objects.create(title='Task 1', due_at=make_aware(datetime(2023, 12, 30, 23, 59)))
        task2 = Task.objects.create(title='Task 2', due_at=make_aware(datetime(2023, 12, 31, 23, 59)))
        
        response = self.client.get(self.url_index + '?order=due')
        self.assertEqual(response.status_code, 200)
        tasks = response.context['tasks']
        self.assertEqual(tasks[0], task1)
        self.assertEqual(tasks[1], task2)

    def test_detail_get_fail(self):
        response = self.client.get(reverse('detail', args=[999])) 
        self.assertEqual(response.status_code, 404)

    def test_detail_get_success(self):
        task = Task.objects.create(title='Task Success', due_at=make_aware(datetime.now()))
        response = self.client.get(reverse('detail', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['task'], task)