#!/usr/bin/env python3
"""
EVO-TR Scheduler Script
========================
Gece analizi için scheduler script.

Kullanım:
    # Manuel çalıştırma
    python scripts/run_analysis.py
    
    # Belirli tarih için
    python scripts/run_analysis.py --date 2024-12-03
    
    # Son N gün için
    python scripts/run_analysis.py --days 7
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lifecycle.async_processor import create_async_processor
from src.lifecycle.logger import create_logger


def run_analysis(date: str, verbose: bool = True):
    """Tek bir gün için analiz çalıştır"""
    if verbose:
        print(f"\n{'='*50}")
        print(f"📊 Running analysis for {date}")
        print('='*50)
    
    processor = create_async_processor()
    results = processor.run_full_analysis(date)
    
    if verbose:
        print(f"\n📈 Results:")
        print(f"  • Total conversations: {results['daily_summary'].get('total_conversations', 0)}")
        print(f"  • Success rate: {results['daily_summary'].get('success_rate', 0):.1%}")
        print(f"  • Failed: {results['failed_conversations']}")
        print(f"  • Patterns: {len(results['patterns'])}")
        print(f"  • Facts extracted: {results['extracted_facts']}")
        
        if results['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in results['recommendations']:
                print(f"  → {rec}")
        
        if results['training_suggestions']:
            print(f"\n📚 Training Suggestions:")
            for sug in results['training_suggestions']:
                print(f"  [{sug['priority']}/5] {sug['category']}: {sug['reason']}")
    
    return results


def run_multi_day_analysis(days: int, verbose: bool = True):
    """Birden fazla gün için analiz çalıştır"""
    all_results = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        results = run_analysis(date, verbose)
        all_results.append(results)
    
    return all_results


def main():
    parser = argparse.ArgumentParser(description="EVO-TR Gece Analizi")
    parser.add_argument("--date", type=str, help="Analiz tarihi (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="Son N gün için analiz")
    parser.add_argument("--quiet", action="store_true", help="Sessiz mod")
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if verbose:
        print("🌙 EVO-TR Night Analysis Started")
        print(f"⏰ Time: {datetime.now().isoformat()}")
    
    try:
        if args.days:
            results = run_multi_day_analysis(args.days, verbose)
            if verbose:
                print(f"\n✅ Completed analysis for {args.days} days")
        else:
            date = args.date or datetime.now().strftime("%Y-%m-%d")
            results = run_analysis(date, verbose)
            if verbose:
                print(f"\n✅ Analysis completed")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
