"""Unit tests for recommendations engine."""
import pytest
from core.recommender import UsageRecommender


@pytest.fixture
def recommender():
    """Create a UsageRecommender instance."""
    return UsageRecommender()


def test_recommender_initialization(recommender):
    """Test recommender initializes correctly."""
    assert recommender.high_bandwidth_threshold == 5 * 1024 * 1024


def test_no_recommendations_for_empty_data(recommender):
    """Test no recommendations for empty data."""
    recommendations = recommender.get_recommendations({}, {'total': 0})
    assert len(recommendations) == 0


def test_high_usage_app_recommendation(recommender):
    """Test recommendation for app using > 50% bandwidth."""
    snapshot = {
        1234: {
            'app_name': 'Chrome',
            'bytes_sent': 5 * 1024 * 1024,  # 5 MB
            'bytes_recv': 5 * 1024 * 1024   # 5 MB
        },
        5678: {
            'app_name': 'Firefox',
            'bytes_sent': 1 * 1024 * 1024,  # 1 MB
            'bytes_recv': 1 * 1024 * 1024   # 1 MB
        }
    }
    
    total_usage = {
        'bytes_sent': 6 * 1024 * 1024,
        'bytes_recv': 6 * 1024 * 1024,
        'total': 12 * 1024 * 1024
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    # Chrome uses 10MB out of 12MB = 83%
    assert len(recommendations) > 0
    assert any('Chrome' in rec for rec in recommendations)
    assert any('83%' in rec or '80%' in rec for rec in recommendations)


def test_sync_services_recommendation(recommender):
    """Test recommendation for background sync services."""
    snapshot = {
        1234: {
            'app_name': 'OneDrive',
            'bytes_sent': 2 * 1024 * 1024,
            'bytes_recv': 2 * 1024 * 1024
        },
        5678: {
            'app_name': 'Dropbox',
            'bytes_sent': 1 * 1024 * 1024,
            'bytes_recv': 1 * 1024 * 1024
        },
        9012: {
            'app_name': 'Chrome',
            'bytes_sent': 3 * 1024 * 1024,
            'bytes_recv': 3 * 1024 * 1024
        }
    }
    
    total_usage = {
        'bytes_sent': 6 * 1024 * 1024,
        'bytes_recv': 6 * 1024 * 1024,
        'total': 12 * 1024 * 1024
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    # Sync services use 6MB out of 12MB = 50%
    assert len(recommendations) > 0
    # Should have recommendation about sync services
    sync_recs = [r for r in recommendations if 'sync' in r.lower()]
    assert len(sync_recs) > 0


def test_system_process_recommendation(recommender):
    """Test recommendation for system processes."""
    snapshot = {
        1234: {
            'app_name': 'svchost',
            'bytes_sent': 3 * 1024 * 1024,
            'bytes_recv': 3 * 1024 * 1024
        },
        5678: {
            'app_name': 'Chrome',
            'bytes_sent': 2 * 1024 * 1024,
            'bytes_recv': 2 * 1024 * 1024
        }
    }
    
    total_usage = {
        'bytes_sent': 5 * 1024 * 1024,
        'bytes_recv': 5 * 1024 * 1024,
        'total': 10 * 1024 * 1024
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    # svchost uses 6MB out of 10MB = 60%
    assert len(recommendations) > 0
    system_recs = [r for r in recommendations if 'System' in r or 'svchost' in r]
    assert len(system_recs) > 0


def test_bandwidth_threshold_recommendation(recommender):
    """Test recommendation when bandwidth exceeds threshold."""
    snapshot = {
        1234: {
            'app_name': 'Chrome',
            'bytes_sent': 3 * 1024 * 1024,
            'bytes_recv': 3 * 1024 * 1024
        }
    }
    
    # Total exceeds default threshold of 5 MB/s
    total_usage = {
        'bytes_sent': 3 * 1024 * 1024,
        'bytes_recv': 3 * 1024 * 1024,
        'total': 6 * 1024 * 1024  # 6 MB/s
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    assert len(recommendations) > 0
    # Should have recommendation about high bandwidth
    high_bw_recs = [r for r in recommendations if 'High bandwidth' in r or 'data saver' in r]
    assert len(high_bw_recs) > 0


def test_multiple_apps_recommendation(recommender):
    """Test recommendation for multiple moderate-usage apps."""
    snapshot = {
        1: {'app_name': 'App1', 'bytes_sent': 1024 * 1024, 'bytes_recv': 1024 * 1024},
        2: {'app_name': 'App2', 'bytes_sent': 1024 * 1024, 'bytes_recv': 1024 * 1024},
        3: {'app_name': 'App3', 'bytes_sent': 1024 * 1024, 'bytes_recv': 1024 * 1024},
        4: {'app_name': 'App4', 'bytes_sent': 500 * 1024, 'bytes_recv': 500 * 1024},
    }
    
    total_usage = {
        'bytes_sent': 3.5 * 1024 * 1024,
        'bytes_recv': 3.5 * 1024 * 1024,
        'total': 7 * 1024 * 1024
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    # Should detect multiple apps each using moderate bandwidth
    assert len(recommendations) > 0


def test_aggregate_by_app(recommender):
    """Test aggregation of usage by app name."""
    snapshot = {
        1234: {'app_name': 'Chrome', 'bytes_sent': 1000, 'bytes_recv': 2000},
        5678: {'app_name': 'Chrome', 'bytes_sent': 500, 'bytes_recv': 1000},
        9012: {'app_name': 'Firefox', 'bytes_sent': 300, 'bytes_recv': 400},
    }
    
    app_usage = recommender._aggregate_by_app(snapshot)
    
    assert 'Chrome' in app_usage
    assert app_usage['Chrome']['bytes_sent'] == 1500
    assert app_usage['Chrome']['bytes_recv'] == 3000
    assert app_usage['Chrome']['total'] == 4500
    assert len(app_usage['Chrome']['pids']) == 2
    
    assert 'Firefox' in app_usage
    assert app_usage['Firefox']['total'] == 700


def test_set_threshold(recommender):
    """Test updating bandwidth threshold."""
    new_threshold = 10 * 1024 * 1024  # 10 MB/s
    recommender.set_threshold(new_threshold)
    
    assert recommender.high_bandwidth_threshold == new_threshold


def test_specific_app_recommendations(recommender):
    """Test specific recommendations for known apps."""
    # Test Chrome recommendation
    snapshot = {
        1234: {
            'app_name': 'Chrome',
            'bytes_sent': 5 * 1024 * 1024,
            'bytes_recv': 5 * 1024 * 1024
        }
    }
    
    total_usage = {
        'bytes_sent': 5 * 1024 * 1024,
        'bytes_recv': 5 * 1024 * 1024,
        'total': 10 * 1024 * 1024
    }
    
    recommendations = recommender.get_recommendations(snapshot, total_usage)
    
    # Should mention Chrome and suggest pausing video or closing tabs
    chrome_recs = [r for r in recommendations if 'Chrome' in r]
    assert len(chrome_recs) > 0
    assert any('video' in r.lower() or 'tabs' in r.lower() for r in chrome_recs)
