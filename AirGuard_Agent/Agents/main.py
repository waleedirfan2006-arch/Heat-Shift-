
from data_quality_agent import DataQualityAgent
from insight_agent import InsightAgent


def main():
    print("\n=== AIRGUARD STARTED ===")

    print("\nStep 1: Checking data quality")
    DataQualityAgent().run()

    print("\nStep 2: Generating insights")
    InsightAgent().run()

    print("\n=== AIRGUARD FINISHED ===")


if __name__ == "__main__":
    main()
