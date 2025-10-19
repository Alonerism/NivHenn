#!/usr/bin/env python3
"""
Quick verification script to test the setup.
Run this to verify all components are working before real analysis.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required packages are installed."""
    print("Testing imports...")
    
    try:
        import httpx
        print("✓ httpx")
    except ImportError:
        print("✗ httpx - run: pip install httpx")
        return False
    
    try:
        import pydantic
        print("✓ pydantic")
    except ImportError:
        print("✗ pydantic - run: pip install pydantic")
        return False
    
    try:
        from pydantic_settings import BaseSettings
        print("✓ pydantic-settings")
    except ImportError:
        print("✗ pydantic-settings - run: pip install pydantic-settings")
        return False
    
    try:
        import tenacity
        print("✓ tenacity")
    except ImportError:
        print("✗ tenacity - run: pip install tenacity")
        return False
    
    try:
        import crewai
        print("✓ crewai")
    except ImportError:
        print("✗ crewai - run: pip install crewai")
        return False
    
    try:
        import fastapi
        print("✓ fastapi")
    except ImportError:
        print("✗ fastapi - run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("✓ uvicorn")
    except ImportError:
        print("✗ uvicorn - run: pip install uvicorn")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv")
    except ImportError:
        print("✗ python-dotenv - run: pip install python-dotenv")
        return False
    
    try:
        from rich import console
        print("✓ rich")
    except ImportError:
        print("✗ rich - run: pip install rich")
        return False
    
    return True


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.app.config import settings
        print("✓ Config loaded")
        
        # Check API keys
        if settings.rapidapi_key and settings.rapidapi_key != "__SET_ME__":
            print("✓ RAPIDAPI_KEY configured")
        else:
            print("⚠ RAPIDAPI_KEY not set - add to .env file")
        
        if settings.openai_api_key and settings.openai_api_key != "__SET_ME__":
            print("✓ OPENAI_API_KEY configured")
        else:
            print("⚠ OPENAI_API_KEY not set - add to .env file")
        
        # Check weights
        weights = settings.get_weights()
        total = sum(weights.values())
        if abs(total - 1.0) < 0.01:
            print(f"✓ Agent weights sum to {total:.2f}")
        else:
            print(f"⚠ Agent weights sum to {total:.2f} (should be 1.0)")
        
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False


def test_models():
    """Test Pydantic models."""
    print("\nTesting models...")
    
    try:
        from src.app.models import SearchParams, AgentOutput, FinalReport
        
        # Test SearchParams
        params = SearchParams(
            locationId="41096",
            locationType="city",
            size=5
        )
        print("✓ SearchParams model")
        
        # Test AgentOutput
        output = AgentOutput(
            score_1_to_100=75,
            rationale="Test rationale",
            notes=["Note 1", "Note 2"]
        )
        print("✓ AgentOutput model")
        
        return True
    except Exception as e:
        print(f"✗ Models error: {e}")
        return False


def test_scoring():
    """Test scoring utilities."""
    print("\nTesting scoring functions...")
    
    try:
        from src.app.scoring import weighted_overall, to_int_1_100, normalize_to_100
        
        # Test to_int_1_100
        assert to_int_1_100(75.6) == 76
        assert to_int_1_100(None) == 50
        assert to_int_1_100(150) == 100
        assert to_int_1_100(-10) == 1
        print("✓ to_int_1_100")
        
        # Test weighted_overall
        scores = {
            "investment": 80,
            "location": 70,
            "news": 60,
            "vc_risk": 75,
            "construction": 65
        }
        weights = {
            "investment": 0.30,
            "location": 0.25,
            "news": 0.10,
            "vc_risk": 0.20,
            "construction": 0.15
        }
        overall = weighted_overall(scores, weights)
        assert 1 <= overall <= 100
        print(f"✓ weighted_overall (result: {overall})")
        
        # Test normalize_to_100
        assert normalize_to_100(50, 0, 100) == 50
        print("✓ normalize_to_100")
        
        return True
    except Exception as e:
        print(f"✗ Scoring error: {e}")
        return False


def test_agents():
    """Test agent creation."""
    print("\nTesting agent creation...")
    
    try:
        from src.agents.investor import create_investor_agent
        from src.agents.location_risk import create_location_agent
        from src.agents.news_reddit import create_news_agent
        from src.agents.vc_risk_return import create_vc_risk_agent
        from src.agents.construction import create_construction_agent
        from src.agents.aggregator import create_aggregator_agent
        
        # Just test that they can be created
        create_investor_agent()
        print("✓ Investment analyst")
        
        create_location_agent()
        print("✓ Location analyst")
        
        create_news_agent()
        print("✓ News analyst")
        
        create_vc_risk_agent()
        print("✓ VC Risk analyst")
        
        create_construction_agent()
        print("✓ Construction analyst")
        
        create_aggregator_agent()
        print("✓ Aggregator")
        
        return True
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Real Estate Scout - Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Models", test_models()))
    results.append(("Scoring", test_scoring()))
    results.append(("Agents", test_agents()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! You're ready to run analysis.")
        print("\nNext steps:")
        print("1. Ensure .env file has valid API keys")
        print("2. Run: python -m src.cli analyze --location-id 41096 --size 3")
        print("   (or)")
        print("   Run: uvicorn src.main:app --reload")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nQuick fix:")
        print("  pip install -e .")
        return 1


if __name__ == "__main__":
    sys.exit(main())
