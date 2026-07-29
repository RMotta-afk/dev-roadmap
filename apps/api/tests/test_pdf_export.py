import pytest

from app.pdf.pdf_export import build_pdf, parse_full_name, _stars, _translate_level


class TestParseFullName:
    def test_two_part_name(self):
        assert parse_full_name("João Silva") == "João_Silva"

    def test_single_name(self):
        assert parse_full_name("Maria") == "Maria"

    def test_three_part_name(self):
        assert parse_full_name("José da Silva") == "José_da_Silva"

    def test_extra_whitespace(self):
        assert parse_full_name("  João   Silva  ") == "João_Silva"

    def test_empty_string(self):
        assert parse_full_name("") == "Usuario"

    def test_whitespace_only(self):
        assert parse_full_name("   ") == "Usuario"

    def test_special_characters(self):
        assert parse_full_name("José André") == "José_André"


class TestTranslateLevel:
    def test_junior(self):
        assert _translate_level("junior") == "Júnior"

    def test_mid(self):
        assert _translate_level("mid") == "Pleno"

    def test_senior(self):
        assert _translate_level("senior") == "Sênior"

    def test_staff(self):
        assert _translate_level("staff") == "Especialista"

    def test_unknown(self):
        assert _translate_level("unknown") == "Desconhecido"

    def test_already_portuguese_ignored(self):
        assert _translate_level("Pleno") == "Pleno"


class TestStars:
    def test_zero_importance(self):
        assert _stars(0) == "☆☆☆☆☆"

    def test_low_importance(self):
        assert _stars(10) == "★☆☆☆☆"

    def test_mid_importance(self):
        assert _stars(40) == "★★☆☆☆"

    def test_high_importance(self):
        assert _stars(80) == "★★★★☆"

    def test_clamped_above_100(self):
        assert _stars(120) == "★★★★★"

    def test_clamped_below_0(self):
        assert _stars(-10) == "☆☆☆☆☆"


class TestBuildPdf:
    def test_valid_pdf_output(self):
        result = {
            "level_resume": {
                "summary": "Desenvolvedor com experiência em Python.",
                "strong_points": ["Python", "Git"],
                "weak_points": ["Docker"],
                "estimated_level": "junior",
            },
            "compatibility_score": 75,
            "personalized_roadmap": [
                {
                    "name": "Docker Básico",
                    "category": "DevOps",
                    "level": "mid",
                    "importance": 85,
                    "description": "Aprender containers.",
                },
            ],
            "errors": [],
        }
        pdf_bytes = build_pdf(result, "João Silva")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_pdf_with_empty_roadmap(self):
        result = {
            "level_resume": {
                "summary": "Sem resumo.",
                "strong_points": [],
                "weak_points": [],
                "estimated_level": "junior",
            },
            "compatibility_score": 50,
            "personalized_roadmap": [],
            "errors": [],
        }
        pdf_bytes = build_pdf(result, "Maria")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_pdf_with_missing_level_resume(self):
        result = {}
        pdf_bytes = build_pdf(result, "Teste")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_pdf_with_errors_section(self):
        result = {
            "level_resume": {
                "summary": "Resumo.",
                "strong_points": [],
                "weak_points": [],
                "estimated_level": "unknown",
            },
            "compatibility_score": 0,
            "personalized_roadmap": [],
            "errors": ["Algum erro de pipeline"],
        }
        pdf_bytes = build_pdf(result, "Usuario")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_pdf_contains_portuguese_content(self):
        result = {
            "level_resume": {
                "summary": "Desenvolvedor júnior focado em frontend.",
                "strong_points": ["JavaScript", "React"],
                "weak_points": ["TypeScript", "Testes"],
                "estimated_level": "junior",
            },
            "compatibility_score": 60,
            "personalized_roadmap": [
                {
                    "name": "TypeScript Avançado",
                    "category": "Frontend",
                    "level": "mid",
                    "importance": 90,
                    "description": "Estudar tipos avançados.",
                },
            ],
            "errors": [],
        }
        pdf_bytes = build_pdf(result, "Ana Costa")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")