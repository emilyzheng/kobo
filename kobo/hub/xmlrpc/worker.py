# -*- coding: utf-8 -*-


from kobo.hub.models import Task
from kobo.hub.decorators import validate_worker


__all__ = (
    "assign_task",
    "open_task",
    "close_task",
    "cancel_task",
    "fail_task",
    "interrupt_tasks",
    "timeout_tasks",

    "get_tasks_to_assign",
    "get_awaited_tasks",
    "get_worker_info",
    "get_worker_id",
    "get_worker_tasks",
    "get_task",
    "get_task_no_verify",

    "set_task_weight",
    "update_worker",
    "create_subtask",
    "wait",
    "check_wait",
)


@validate_worker
def get_worker_info(request):
    """Get information about a worker.
        @return: dict
    """
    return request.worker.export()


@validate_worker
def get_worker_id(request):
    """Get worker ID of a worker.
        @return: int
    """
    return request.worker.id


@validate_worker
def get_worker_tasks(request):
    """Get list of tasks running on a worker.
        @return: list
    """
    task_list = []
    for task in request.worker.running_tasks().order_by("-exclusive", "-awaited", "id"):
        task_info = task.export()

        # set wakeup alert
        if task.waiting:
            finished, unfinished = task.check_wait()
            if len(finished) > 0:
                task_info["alert"] = True

        task_list.append(task_info)
    return task_list


@validate_worker
def get_task(request, task_id):
    """Get information about a task.
        @param task_id: a task ID
        @type  task_id: int
        @return: dict
    """
    task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
    return task.export()


@validate_worker
def get_task_no_verify(request, task_id):
    """Get information about a task, do not verify whether is assigned to a worker.
        @param task_id: a task ID
        @type  task_id: int
        @return: dict
    """
    task = Task.objects.get(id=task_id)
    return task.export()


@validate_worker
def interrupt_tasks(request, task_list):
    result = True
    for task_id in task_list:
        task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
        if task:
            try:
                task.interrupt_task(recursive=True)
            except:
                raise
                result = False
    return result


@validate_worker
def timeout_tasks(request, task_list):
    result = True
    for task_id in task_list:
        task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
        if task:
            try:
                task.timeout_task(recursive=True)
            except:
                raise
                result = False
    return result


@validate_worker
def assign_task(request, task_id):
    task = Task.objects.get(id=task_id)
    return task.assign_task(request.worker.id)


@validate_worker
def open_task(request, task_id):
    task = Task.objects.get(id=task_id)
    return task.open_task(request.worker.id)


@validate_worker
def close_task(request, task_id, result=None):
    task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
    return task.close_task(result)


@validate_worker
def cancel_task(request, task_id):
    task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
    return task.cancel_task()


@validate_worker
def fail_task(request, task_id, result=None, traceback=None):
    task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
    return task.fail_task(result, traceback)


@validate_worker
def set_task_weight(request, task_id, weight):
    task = Task.objects.get_and_verify(task_id=task_id, worker=request.worker)
    task.setWeight(weight)
    return task.weight


@validate_worker
def update_worker(request, enabled, ready, task_count):
    return request.worker.update_worker(enabled, ready, task_count)


@validate_worker
def get_tasks_to_assign(request):
    task_list = []

    # all exclusive tasks
    for task in request.worker.assigned_tasks().filter(exclusive=True).order_by("id"):
        task_info = task.export(flat=False)
        task_list.append(task_info)

    # all awaited tasks
    for task in Task.objects.free().filter(awaited=True).order_by("id"):
        task_info = task.export(flat=False)
        task_list.append(task_info)

    # first 50 tasks assigned to this worker
    for task in request.worker.assigned_tasks().filter(exclusive=False).order_by("id")[:50]:
        task_info = task.export(flat=False)
        task_list.append(task_info)

    # first 50 free tasks, ordered by priority
    for task in Task.objects.free().filter(awaited=False).order_by("-priority", "id")[:50]:
        task_info = task.export(flat=False)
        task_list.append(task_info)

    return task_list


@validate_worker
def get_awaited_tasks(request, awaited_task_list):
    task_list = []
    for task in Task.objects.filter(awaited=True, parent__in=[ i["id"] for i in awaited_task_list ]):#.order_by("-exclusive", "-awaited", "id")[:50]:
        task_info = task.export()
        task_list.append(task_info)
    return task_list


@validate_worker
def create_subtask(request, label, method, args, parent_id):
    parent_task = Task.objects.get_and_verify(task_id=parent_id, worker=request.worker)
#    def create_task(cls, owner_name, label, method, args=None, parent_id=None, worker_name=None, arch_name="noarch", channel_name="default", priority=10, weight=1, exclusive=False):
#    subtask_id = self.__hub.worker.createSubtask(label, method, args, self.__task_id)
    return Task.create_task(parent_task.owner.username, label, method, args, parent_id)#, arch=parent_task.arch, channel=parent_task.channel, priority=priority, weight=weight)


@validate_worker
def wait(request, task_id, child_list=None):
    task = Task.objects.get(id=task_id)
    task.wait(child_list)
    return True


@validate_worker
def check_wait(request, task_id, child_list=None):
    task = Task.objects.get(id=task_id)
    return task.check_wait(child_list)
