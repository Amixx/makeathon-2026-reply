from __future__ import annotations

# (pattern, spoken response)  — checked in order, first match wins
REGEX_RESPONSES: list[tuple[str, str]] = [
    # Technical fields
    (
        r"\bcomputer\s*science\b|\bCS\b|\bsoftware\s*engin",
        "Hmm, computer science — there are so many directions you can take that, it really depends on what pulls you most.",
    ),
    (
        r"\bmachine\s*learning\b|\bdeep\s*learning\b|\bneural\s*network|\bML\b",
        "Machine learning — yeah, that space is moving incredibly fast, and the demand is still way ahead of supply.",
    ),
    (
        r"\bartificial\s*intelligence\b|\bAI\b|\bLLM\b|\blarge\s*language",
        "AI is such a broad space right now — it means something different depending on whether you're building it or applying it.",
    ),
    (
        r"\bdata\s*science\b|\bdata\s*analy|\bdata\s*engin|\banalytics\b",
        "Data — interesting. The field has matured a lot, and companies are getting more specific about what skills they actually need.",
    ),
    (
        r"\bproduct\s*manag|\bPM\b|\bproduct\s*owner",
        "Product management — so you're drawn to the intersection of tech and people, where you're shaping what actually gets built.",
    ),
    (
        r"\bresearch\b|\bPhD\b|\bacademia\b|\bprofessor\b|\bpublish",
        "Research and academia — going deep rather than broad. That tells me something about how you like to work.",
    ),
    (
        r"\bconsult|\bMcKinsey\b|\bBCG\b|\bBain\b|\bstrategy\s*consult",
        "Consulting — high exposure early on, and you get to see a lot of different industries in a short amount of time.",
    ),
    (
        r"\bfinance\b|\bbanking\b|\binvestment\b|\btrading\b|\bfintech\b|\bhedge\s*fund",
        "Finance — there's a huge range there, from traditional investment banking all the way to fintech startups.",
    ),
    (
        r"\bhealthcare\b|\bmedicine\b|\bbiotech\b|\bpharma\b|\bmedical\b|\bhealth\s*tech",
        "Healthcare and biotech — a space where technical skills can have genuinely meaningful real-world impact.",
    ),
    (
        r"\bsustainab|\bclimate\b|\bgreen\s*tech|\brenewable|\bclean\s*energy",
        "Sustainability — there's real momentum there, and entirely new categories of roles are opening up.",
    ),
    (
        r"\bdesign\b|\bUX\b|\bUI\b|\buser\s*experience\b|\bcreative\b|\bvisual",
        "Design and UX — combining creativity with deep user empathy. That's actually a rare and valuable combination.",
    ),
    # Emotions and attitudes
    (
        r"\bexcited\b|\bpassionat|\blove\s+(?:to|work|\w+ing)|\bfascinat|\breally\s+enjoy",
        "I can hear the genuine enthusiasm in that — that kind of energy is actually one of the best signals we have.",
    ),
    (
        r"\bnot\s+sure\b|\buncertain|\bdon'?t\s+know|\bunsure\b|\bfiguring\s+out|\bconfused\b",
        "Totally fine to be figuring that out — honestly, most people are at this stage, and that's exactly what we're here to work through.",
    ),
    (
        r"\bnervous\b|\bworried\b|\banxious\b|\bscared\b|\bafraid\b|\bintimidated",
        "That's a really honest thing to say, and it's more common than people let on. Let's see what's driving that.",
    ),
    (
        r"\bchallenging\b|\bdifficult\b|\bstruggle|\bhard\s+to\b|\btough\b|\bhaven'?t\s+been\s+able",
        "Yeah, that's a real friction point — it's worth digging into what's actually behind it.",
    ),
    # Context and constraints
    (
        r"\bstartup\b|\bfounding\b|\bentrepreneur|\bbuild\s+(?:a|my|our|your)\s+(?:company|startup|product)|\bown\s+company",
        "Startup world — that says something about how you like to operate: fast-moving, high ownership, building from scratch.",
    ),
    (
        r"\bvisa\b|\bwork\s+permit\b|\bresidency\b|\bimmigrat|\bsponsored\b|\bwork\s+authoriz",
        "Visa situation — yeah, that shapes a lot of decisions, especially when you're looking across borders.",
    ),
    (
        r"\bsalar|\bmoney\b|\bincome\b|\bpay\b|\bfinancial\b|\bcompensation\b|\bafford",
        "Financial goals are completely valid to factor in — there's no reason to separate that from your career direction.",
    ),
    (
        r"\bremote\b|\blocation\b|\bBerlin\b|\bMunich\b|\bLondon\b|\bNew\s+York\b|\brelocat|\bwork\s+from\s+home",
        "Location preferences matter more than people admit — it's good to be honest about what actually works for your life.",
    ),
    (
        r"\bPython\b|\bcoding\b|\bprogramming\b|\bdeveloper\b|\bsoftware\s+build|\bopen\s+source",
        "Strong hands-on technical background — that opens a lot of doors, and it compounds over time.",
    ),
    (
        r"\bTUM\b|\buniversity\b|\bmaster'?s?\b|\bbachelor'?s?\b|\bmy\s+degree\b|\bmy\s+studies\b",
        "Your time at TUM gives you a solid foundation — there's quite a lot you can leverage from that, often more than people realize.",
    ),
    (
        r"\binternship\b|\bintern\b|\bworking\s+student\b|\bpart.time\b|\bwerkstudent",
        "Hands-on experience like that really stands out — it shows initiative beyond the classroom and gives you something concrete to point to.",
    ),
    # Skills and qualities
    (
        r"\bleadership\b|\bmanag(?:ing|ement)\b|\blead(?:ing)?\s+a\s+team|\bpeople\s+manag",
        "So leading people is part of what you're drawn to — not just the technical work, but the human side of building things.",
    ),
    (
        r"\bproject\b|\bbuilt\b|\bcreated\b|\bdeveloped\b|\bworked\s+on\b|\bshipped\b|\blaunched\b",
        "That kind of real project experience is exactly what employers want to see — it shows you can take something from idea to reality.",
    ),
    (
        r"\bmentor\b|\bguidance\b|\badvice\b|\bdirection\b|\bsomeone\s+to\s+help|\bcoach",
        "It sounds like having the right guidance and clarity could make a real difference for you at this stage.",
    ),
]


GENERIC_FILLERS: list[str] = [
    "Let me think about that for a moment...",
    "That's really helpful context, thank you for sharing.",
    "Okay, I'm processing that — give me just a second.",
    "Interesting, that gives me a much clearer picture.",
    "Right, so let me work through what that means for your path...",
    "Good to know — I'm definitely taking that into account.",
    "That makes a lot of sense. Let me think about the best follow-up.",
    "Noted. I want to make sure I ask you the right thing next.",
    "Alright, that's a really useful data point.",
    "I appreciate you being open about that. One moment.",
    "Okay, I hear you. Let me think about where to take this.",
    "That adds some important context. Thinking through it...",
    "Understood. Let me build on what you just said.",
    "Good — I'm connecting that to what you mentioned earlier.",
    "That's helpful. I want to make sure the next question is the right one.",
]
