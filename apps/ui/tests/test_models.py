from ui.api.models import normalize_result_payload


def test_normalize_level_estimate():
    result = normalize_result_payload(
        {
            "level_estimate": "mid",
            "compatibility_score": 80,
            "personalized_roadmap": [
                {
                    "id": "n1",
                    "name": "Python",
                    "type": "skill",
                    "category": "lang",
                    "level": "mid",
                    "importance": 8,
                }
            ],
        }
    )
    assert result.level_resume.estimated_level == "mid"
    assert result.compatibility_score == 80
    assert len(result.personalized_roadmap) == 1
    assert result.personalized_roadmap[0].name == "Python"


def test_normalize_level_resume():
    result = normalize_result_payload(
        {
            "level_resume": {
                "summary": "Solid mid",
                "strong_points": ["Python"],
                "weak_points": ["K8s"],
                "estimated_level": "mid",
            },
            "compatibility_score": 50,
            "personalized_roadmap": [],
        }
    )
    assert result.level_resume.summary == "Solid mid"
    assert result.level_resume.strong_points == ["Python"]
