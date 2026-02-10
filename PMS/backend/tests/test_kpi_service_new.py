
import pytest
from datetime import datetime, timedelta, timezone
from app.models.task import Task, TaskStatus
from app.services.kpi_service import calculate_timeliness, calculate_score

# Mock settings
class MockSettings:
    penalty_factor = 1.0
    min_timeliness = 0.2
    base_score = 10.0

import app.services.kpi_service
app.services.kpi_service.settings = MockSettings()

def test_calculate_timeliness_on_time():
    now = datetime.now(timezone.utc)
    task = Task(
        plan_start=now - timedelta(days=5),
        plan_end=now + timedelta(days=5),
        actual_end=now, # Completed early
        status=TaskStatus.COMPLETED
    )
    assert calculate_timeliness(task) == 1.0

def test_calculate_timeliness_overdue():
    now = datetime.now(timezone.utc)
    # Duration = 10 days
    # Overdue = 2 days
    # T = 1.0 - (2 / 10) * 1.0 = 0.8
    task = Task(
        plan_start=now - timedelta(days=12),
        plan_end=now - timedelta(days=2),
        actual_end=now,
        status=TaskStatus.COMPLETED
    )
    assert calculate_timeliness(task) == pytest.approx(0.8)

def test_calculate_timeliness_severe_overdue():
    now = datetime.now(timezone.utc)
    # Duration = 10 days
    # Overdue = 20 days
    # T = 1.0 - (20 / 10) = -1.0 -> should be min 0.2
    task = Task(
        plan_start=now - timedelta(days=30),
        plan_end=now - timedelta(days=20),
        actual_end=now,
        status=TaskStatus.COMPLETED
    )
    assert calculate_timeliness(task) == 0.2

def test_calculate_score_main_task():
    # B=10 (default), I=1.0, D=1.0, Q=1.0, T=1.0, P=0
    # Score = 10 * 1 * 1 * 1 * 1 = 10
    task = Task(
        workload_b=0.0,
        importance_i=1.0,
        difficulty_d=1.0,
        quality_q=1.0,
        progress=100,
        status=TaskStatus.COMPLETED
    )
    # Mock timeliness check or ensure task data produces T=1.0
    task.plan_start = datetime.now(timezone.utc) - timedelta(days=2)
    task.plan_end = datetime.now(timezone.utc) + timedelta(days=2)
    task.actual_end = datetime.now(timezone.utc)
    
    assert calculate_score(task) == 10.0

def test_calculate_score_subtask():
    # B=50, I=1.2, D=1.1, Q=0.9, T=0.8
    # Score = 50 * 1.2 * 1.1 * 0.9 * 0.8 = 47.52
    
    parent = Task(importance_i=1.2, difficulty_d=1.1)
    
    now = datetime.now(timezone.utc)
    task = Task(
        workload_b=50.0,
        parent=parent,
        quality_q=0.9,
        progress=100,
        status=TaskStatus.COMPLETED,
        plan_start=now - timedelta(days=10),
        plan_end=now - timedelta(days=2), # Due 2 days ago
        actual_end=now # Completed now
    )
    # Duration=8, Overdue=2. T = 1 - 2/8 = 0.75
    # Score = 50 * 1.2 * 1.1 * 0.9 * 0.75 = 44.55
    
    expected_score = 50 * 1.2 * 1.1 * 0.9 * 0.75
    assert calculate_score(task) == pytest.approx(expected_score)
