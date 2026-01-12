#!/usr/bin/env python3
# run_entity_demo.py
"""
Entity Resolution Demo

A standalone demo script to test entity resolution with sample Reddit posts.
Demonstrates the complete entity resolution pipeline:
1. Extract entities from posts
2. Resolve to canonical forms
3. Display results in CLI
4. Generate HTML report

Usage:
    python run_entity_demo.py
    python run_entity_demo.py --output report.html
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "entity")
)

# Import entity modules
from entity_resolver import EntityResolver
from entity_extractor import EntityExtractor
from entity_browser import EntityBrowser
from entity_report import generate_html_report


# Sample Reddit posts for demo
SAMPLE_POSTS = [
    {
        "id": "demo1",
        "title": "OpenAI releases GPT-4 Turbo with 128K context window",
        "selftext": """Sam Altman announced that OpenAI has released GPT-4 Turbo today. 
        The new model supports up to 128K tokens and is significantly cheaper than GPT-4.
        ChatGPT Plus users will get access to the new model soon.
        Microsoft is expected to integrate this into Copilot as well.""",
        "subreddit": "MachineLearning",
        "permalink": "/r/MachineLearning/comments/demo1",
    },
    {
        "id": "demo2",
        "title": "Comparing ChatGPT vs Claude vs Gemini for coding tasks",
        "selftext": """I tested chat gpt, Claude 3 Opus, and Google Gemini Pro on various coding tasks.
        The company behind ChatGPT (Open AI) has the best reasoning, but Anthropic's Claude 
        is catching up fast. Dario Amodei's team has done impressive work.
        Gemini is good but feels less polished than the others.""",
        "subreddit": "artificial",
        "permalink": "/r/artificial/comments/demo2",
    },
    {
        "id": "demo3",
        "title": "Elon Musk criticizes OpenAI again on Twitter",
        "selftext": """@elonmusk tweeted about @OpenAI again today. Musk says the company has 
        strayed from its original nonprofit mission. Altman has not responded yet.
        This ongoing feud between Elon and OpenAI continues...""",
        "subreddit": "technology",
        "permalink": "/r/technology/comments/demo3",
    },
    {
        "id": "demo4",
        "title": "DALL-E 3 vs Midjourney v6 vs Stable Diffusion XL comparison",
        "selftext": """I compared DALLE 3, MidJourney v6, and SDXL for various image generation tasks.
        OpenAI's DALL-E has the best prompt understanding. Midjourney produces the most artistic results.
        Stable Diffusion is the most flexible for fine-tuning.""",
        "subreddit": "StableDiffusion",
        "permalink": "/r/StableDiffusion/comments/demo4",
    },
    {
        "id": "demo5",
        "title": "Microsoft Copilot now uses GPT-4 Turbo",
        "selftext": """Satya Nadella confirmed that Microsoft Copilot is now powered by GPT4 Turbo.
        The integration between Microsoft and openai continues to deepen.
        GitHub Copilot will also get the upgrade soon.""",
        "subreddit": "OpenAI",
        "permalink": "/r/OpenAI/comments/demo5",
    },
    {
        "id": "demo6",
        "title": "Local LLMs are getting really good - LLaMA 2 vs Mistral comparison",
        "selftext": """I've been running Llama 2 70B and Mistral 7B locally. Both are impressive.
        Meta's LLaMA models have come a long way. Mistral AI is the new kid on the block
        but already competitive with much larger models.""",
        "subreddit": "LocalLLaMA",
        "permalink": "/r/LocalLLaMA/comments/demo6",
    },
    {
        "id": "demo7",
        "title": "Anthropic raises $2B, Claude 3 coming soon",
        "selftext": """Anthropic just raised another $2 billion. The company behind Claude AI
        is now valued at $18B. Dario Amodei said Claude 3 will be released soon.
        Google and Amazon are major investors in Anthropic.""",
        "subreddit": "singularity",
        "permalink": "/r/singularity/comments/demo7",
    },
    {
        "id": "demo8",
        "title": "The AI race heats up - Google, Microsoft, Meta all competing",
        "selftext": """The competition between Google, Microsoft, and Meta in AI is intense.
        Sundar Pichai announced Gemini Ultra, Satya Nadella is pushing Copilot everywhere,
        and Mark Zuckerberg released LLaMA 2 as open source.
        Meanwhile, OpenAI and Anthropic continue to lead in capabilities.""",
        "subreddit": "Futurology",
        "permalink": "/r/Futurology/comments/demo8",
    },
]


def run_demo(output_file: str = None, interactive: bool = False):
    """Run the entity resolution demo"""

    print("\n" + "=" * 70)
    print("🏷️  ENTITY RESOLUTION DEMO")
    print("=" * 70)
    print(f"\nProcessing {len(SAMPLE_POSTS)} sample Reddit posts...")

    # Step 1: Extract entities
    print("\n" + "-" * 50)
    print("Step 1: Extracting entities from posts...")
    print("-" * 50)

    extractor = EntityExtractor()
    resolver = extractor.extract_from_posts(SAMPLE_POSTS)

    # Step 2: Display results
    print("\n" + "-" * 50)
    print("Step 2: Resolved Entities")
    print("-" * 50)

    # Organizations
    orgs = resolver.get_entities_by_type("ORG")
    print(f"\n🏢 ORGANIZATIONS ({len(orgs)}):")
    for entity in orgs[:8]:
        print(
            f"   • {entity.canonical_name} ({entity.mention_count} mentions, {entity.avg_confidence:.0%} confidence)"
        )
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:4])}")

    # People
    people = resolver.get_entities_by_type("PERSON")
    print(f"\n👤 PEOPLE ({len(people)}):")
    for entity in people[:8]:
        print(
            f"   • {entity.canonical_name} ({entity.mention_count} mentions, {entity.avg_confidence:.0%} confidence)"
        )
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:4])}")

    # Products
    products = resolver.get_entities_by_type("PRODUCT")
    print(f"\n📦 PRODUCTS ({len(products)}):")
    for entity in products[:8]:
        print(
            f"   • {entity.canonical_name} ({entity.mention_count} mentions, {entity.avg_confidence:.0%} confidence)"
        )
        if entity.aliases:
            print(f"     Aliases: {', '.join(entity.aliases[:4])}")

    # Step 3: Show detailed example
    print("\n" + "-" * 50)
    print("Step 3: Detailed Example - Entity Resolution in Action")
    print("-" * 50)

    # Find OpenAI entity
    openai_entity = resolver.get_entity("OpenAI")
    if openai_entity:
        print(f"\n📋 Detailed view: {openai_entity.canonical_name}")
        print(f"   Type: {openai_entity.entity_type}")
        print(f"   Total mentions: {openai_entity.mention_count}")
        print(f"   Aliases resolved: {', '.join(openai_entity.aliases)}")
        print(
            f"   Found in subreddits: {', '.join(openai_entity.subreddits_mentioned_in)}"
        )

        print(f"\n   Sample mentions:")
        for i, mention in enumerate(openai_entity.mentions[:5], 1):
            print(f'\n   [{i}] Raw text: "{mention.raw_text}"')
            print(f'       → Resolved to: "{mention.canonical_name}"')
            print(
                f"       Confidence: {mention.confidence:.0%} (method: {mention.match_method})"
            )
            print(f"       Context: ...{mention.context[:60]}...")

    # Step 4: Generate HTML report
    if output_file:
        print("\n" + "-" * 50)
        print("Step 4: Generating HTML Report")
        print("-" * 50)

        generate_html_report(
            resolver, company_name="AI Companies", output_file=output_file
        )
        print(
            f"\n   Open {output_file} in your browser to view the interactive report!"
        )

    # Summary
    summary = resolver.get_summary()
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"\n   Total unique entities: {summary['total_entities']}")
    print(f"   Total mentions resolved: {summary['total_mentions']}")
    print(f"   Entity types: {summary['by_type']}")

    print("\n   This demonstrates how entity resolution works:")
    print("   • 'OpenAI', 'Open AI', 'openai', '@openai' → all resolved to 'OpenAI'")
    print("   • 'ChatGPT', 'chat gpt', 'Chat GPT' → all resolved to 'ChatGPT'")
    print("   • 'Sam Altman', 'Altman', '@sama' → all resolved to 'Sam Altman'")
    print("   • Each match has a confidence score based on how it was matched")

    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70 + "\n")

    # Interactive mode
    if interactive:
        print("\nStarting interactive browser...")
        browser = EntityBrowser(resolver)
        browser.run()

    return resolver


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entity Resolution Demo")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="entity_report.html",
        help="Output HTML file (default: entity_report.html)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Start interactive browser after demo",
    )

    args = parser.parse_args()

    run_demo(output_file=args.output, interactive=args.interactive)
