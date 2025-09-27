#!/usr/bin/env python3
"""Example usage of BatchScraper for production scenarios."""

import asyncio
import logging
from pathlib import Path

from regscraper.batch import BatchScraper, scrape_urls_batch

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def example_batch_scraping():
    """Example of batch scraping with proper rate limiting."""
    # Example: Mixed URLs from different domains
    urls = [
        # SEC.gov URLs (will be throttled to 2.0s delay, 1 concurrent)
        "https://www.sec.gov/newsroom/press-releases/2025-126-sec-seeks-public-comment-improve-rules-residential-mortgage-backed-securities-asset-backed",
        "https://www.sec.gov/newsroom/press-releases/2025-125-sec-announces-departure-chief-operating-officer-ken-johnson",
        "https://www.sec.gov/newsroom/press-releases/2025-124-sec-announces-agenda-panelists-sec-cftc-roundtable-regulatory-harmonization-efforts",
        # BIS.org URLs (will be throttled to 1.5s delay, 2 concurrent)
        "https://www.bis.org/press/p240101.htm",
        "https://www.bis.org/press/p240102.htm",
        # Other domains (will use default 2.0s delay, 2 concurrent)
        "https://www.treasury.gov/press-center/press-releases/Pages/default.aspx",
    ]

    print("🚀 Example 1: Simple batch processing")
    results = await scrape_urls_batch(
        urls=urls,
        max_concurrent=5,  # Global limit across all domains
    )

    # Show results summary
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

    for result in successful:
        print(f"  📄 {result['url'][:60]}... -> {result['text_length']} chars")


async def example_custom_configuration():
    """Example with custom domain configurations."""
    # Custom site configurations for your specific needs
    custom_site_overrides = {
        # SEC: Very conservative (regulatory site)
        "sec.gov": {
            "delay": 3.0,  # 3 second delay
            "concurrency": 1,  # Only 1 request at a time
            "type": "static",
        },
        # BIS: Moderate throttling
        "bis.org": {
            "delay": 1.5,  # 1.5 second delay
            "concurrency": 2,  # 2 concurrent requests
            "type": "static",
        },
        # Federal Register: More permissive
        "federalregister.gov": {
            "delay": 1.0,  # 1 second delay
            "concurrency": 3,  # 3 concurrent requests
            "type": "static",
        },
        # Treasury: Conservative
        "treasury.gov": {
            "delay": 2.5,  # 2.5 second delay
            "concurrency": 1,  # Only 1 request at a time
            "type": "static",
        },
    }

    print("\n🚀 Example 2: Custom domain configurations")

    # Create scraper with custom configuration
    scraper = BatchScraper(
        site_overrides=custom_site_overrides,
        default_delay=2.0,  # For domains not in overrides
        default_concurrency=2,
        user_agent="MyCompany Scraper/1.0",
    )

    # Example URLs for your use case
    production_urls = [
        # Add your actual URLs here
        "https://www.sec.gov/some-document-1",
        "https://www.sec.gov/some-document-2",
        "https://www.bis.org/some-document-1",
        "https://www.bis.org/some-document-2",
        "https://www.treasury.gov/some-document-1",
        # ... hundreds more
    ]

    # For demo, let's use a smaller set
    demo_urls = [
        "https://www.sec.gov/newsroom/press-releases/2025-126-sec-seeks-public-comment-improve-rules-residential-mortgage-backed-securities-asset-backed",
        "https://www.bis.org/press/p240101.htm",
        "https://www.treasury.gov/press-center/press-releases/Pages/default.aspx",
    ]

    # Process with custom configuration
    results = await scraper.scrape_urls(
        urls=demo_urls,
        output_format="json",
        output_dir=Path("./scraping_results"),
        max_concurrent=8,  # Global limit across all domains
        save_individually=True,
    )

    print(f"✅ Processed {len(results)} URLs with custom throttling")


async def example_large_scale_processing():
    """Example for processing hundreds of URLs."""
    print("\n🚀 Example 3: Large-scale processing simulation")

    # Simulate hundreds of URLs across multiple domains
    large_url_list = []

    # Add SEC URLs (they'll be throttled heavily)
    sec_base = "https://www.sec.gov/newsroom/press-releases/2025-"
    for i in range(126, 100, -1):  # Simulate recent press releases
        large_url_list.append(f"{sec_base}{i}-simulated-url")

    # Add BIS URLs (moderate throttling)
    bis_base = "https://www.bis.org/press/p2024"
    for i in range(1, 21):  # Simulate 20 BIS documents
        large_url_list.append(f"{bis_base}{i:02d}.htm")

    # Add Treasury URLs
    treasury_urls = [
        "https://www.treasury.gov/press-center/press-releases/Pages/jy0001.aspx",
        "https://www.treasury.gov/press-center/press-releases/Pages/jy0002.aspx",
    ]
    large_url_list.extend(treasury_urls)

    print(f"📊 Simulating processing of {len(large_url_list)} URLs")
    print(f"   - SEC URLs: {len([u for u in large_url_list if 'sec.gov' in u])}")
    print(f"   - BIS URLs: {len([u for u in large_url_list if 'bis.org' in u])}")
    print(f"   - Treasury URLs: {len([u for u in large_url_list if 'treasury.gov' in u])}")

    # Create production-ready scraper
    scraper = BatchScraper(default_delay=2.0, default_concurrency=2, user_agent="Production Scraper/1.0")

    # Note: For demo, we'll only process first 5 URLs
    # In production, remove this limitation
    demo_urls = large_url_list[:5]

    print(f"📊 Processing first {len(demo_urls)} URLs as demo...")

    try:
        results = await scraper.scrape_urls(
            urls=demo_urls,
            max_concurrent=10,  # Reasonable global limit
            output_format="json",
        )

        # Analyze timing and success rates
        successful = [r for r in results if r["success"]]
        print(f"✅ Success rate: {len(successful)}/{len(demo_urls)} ({100 * len(successful) / len(demo_urls):.1f}%)")

        # Show domain-wise stats
        domains = {}
        for result in results:
            from urllib.parse import urlparse

            domain = urlparse(result["url"]).netloc.lower()
            if domain not in domains:
                domains[domain] = {"success": 0, "total": 0}
            domains[domain]["total"] += 1
            if result["success"]:
                domains[domain]["success"] += 1

        for domain, stats in domains.items():
            success_rate = 100 * stats["success"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  📊 {domain}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    except Exception as e:
        print(f"❌ Large scale processing failed: {e}")


# Production template for your use case
async def your_production_workflow():
    """Template for your actual production use case."""
    print("\n🚀 Your Production Workflow Template")

    # Step 1: Define your URLs
    your_urls = [
        # Replace with your actual URLs
        # "https://www.sec.gov/your-document-1",
        # "https://www.bis.org/your-document-2",
        # ... hundreds more
    ]

    # Step 2: Configure domain-specific settings
    your_site_config = {
        # Adjust these based on each site's robots.txt and terms
        "sec.gov": {"delay": 2.0, "concurrency": 1, "type": "static"},
        "bis.org": {"delay": 1.5, "concurrency": 2, "type": "static"},
        "treasury.gov": {"delay": 2.0, "concurrency": 1, "type": "static"},
        "federalregister.gov": {"delay": 1.0, "concurrency": 2, "type": "static"},
        # Add more domains as needed
    }

    # Step 3: Create scraper
    scraper = BatchScraper(
        site_overrides=your_site_config,
        default_delay=2.0,  # Conservative default
        user_agent="YourCompany Scraper/1.0 (contact@yourcompany.com)",
    )

    # Step 4: Process in batches if you have hundreds/thousands of URLs
    batch_size = 50  # Process 50 at a time
    all_results = []

    # For demo, we'll simulate just one batch
    # for i in range(0, len(your_urls), batch_size):
    #     batch_urls = your_urls[i:i+batch_size]
    #     batch_results = await scraper.scrape_urls(
    #         urls=batch_urls,
    #         output_dir=Path(f"./results/batch_{i//batch_size:03d}"),
    #         max_concurrent=10,
    #         save_individually=True
    #     )
    #     all_results.extend(batch_results)
    #     print(f"Completed batch {i//batch_size + 1}")

    print("📝 Production workflow template ready!")
    print("   1. Replace 'your_urls' with your actual URL list")
    print("   2. Adjust site configurations based on robots.txt")
    print("   3. Set appropriate batch sizes for your scale")
    print("   4. Configure output directories and formats")
    print("   5. Add error handling and retry logic as needed")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(example_batch_scraping())
    asyncio.run(example_custom_configuration())
    asyncio.run(example_large_scale_processing())
    asyncio.run(your_production_workflow())
