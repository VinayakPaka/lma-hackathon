import { useState } from 'react'
import './index.css'

// Icons as SVG components
const UploadIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
)

const AnalyzeIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
        <path d="M11 8v6" />
        <path d="M8 11h6" />
    </svg>
)

const ReportIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
)

const LinkedInIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
)

const PlusIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
)

// Agent Icons
const AgentIcon = ({ children }) => (
    <div className="agent-icon">
        {children}
    </div>
)

function App() {
    const [openFaq, setOpenFaq] = useState(null)

    const toggleFaq = (index) => {
        setOpenFaq(openFaq === index ? null : index)
    }

    const faqs = [
        {
            question: "What is GreenGuard?",
            answer: "GreenGuard is an AI-powered sustainability assessment platform that helps financial institutions evaluate and validate green lending claims with regulatory compliance."
        },
        {
            question: "How does the AI assessment work?",
            answer: "Our 17 specialized AI agents replicate a banker's analytical brain, processing company sustainability reports, KPIs, and green claims to deliver comprehensive assessments in 15-30 minutes."
        },
        {
            question: "What regulations does GreenGuard support?",
            answer: "GreenGuard is built for EU Taxonomy, CSRD, SFDR, and other major sustainability reporting frameworks, ensuring your assessments meet regulatory requirements."
        },
        {
            question: "How accurate are the AI assessments?",
            answer: "Our AI agents cross-reference multiple data sources, peer benchmarks, and regulatory standards to provide auditable, evidence-based assessments with full transparency."
        },
        {
            question: "Can I integrate GreenGuard with existing systems?",
            answer: "Yes, GreenGuard offers API integration capabilities and can be seamlessly integrated into your existing lending workflows and systems."
        },
        {
            question: "What does the assessment include?",
            answer: "Each assessment includes KPI evaluation, peer benchmarking, regulatory compliance checks, risk analysis, and a comprehensive report with actionable recommendations."
        }
    ]

    const agents = [
        { name: "Scope Analysis", description: "Analyzes emission scopes and boundaries" },
        { name: "Target Validation", description: "Validates reduction targets against SBTi" },
        { name: "Pathway Assessment", description: "Evaluates decarbonization pathways" },
        { name: "Peer Benchmarking", description: "Compares against industry peers" },
        { name: "Risk Evaluation", description: "Identifies greenwashing risks" },
        { name: "Evidence Synthesis", description: "Compiles supporting evidence" },
        { name: "Compliance Check", description: "Validates regulatory alignment" },
        { name: "Report Generation", description: "Creates comprehensive reports" },
    ]

    return (
        <div className="landing-page">
            {/* Announcement Bar */}
            <div className="announcement-bar">
                Revolutionizing Green Lending with AI-Powered Assessments. <a href="#demo">Learn more →</a>
            </div>

            {/* Navigation */}
            <nav className="navbar">
                <div className="navbar-container">
                    <a href="#" className="navbar-brand">
                        <img src="/logo.png" alt="GreenGuard" className="navbar-logo" />
                        <span className="navbar-brand-text">GreenGuard</span>
                    </a>
                    <div className="navbar-links">
                        <a href="#features" className="navbar-link">Features</a>
                        <a href="#how-it-works" className="navbar-link">How It Works</a>
                        <a href="#agents" className="navbar-link">AI Agents</a>
                        <a href="#faq" className="navbar-link">FAQ</a>
                    </div>
                    <div className="navbar-actions">
                        <a href="#demo" className="navbar-cta">Demo</a>
                        <a href="https://greenguard-lma.vercel.app/login" className="navbar-login">Login</a>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="hero">
                <div className="hero-container">
                    <div className="hero-content">
                        <h1 className="hero-title">
                            Transform Green Lending<br />
                            with AI-Powered Assessment
                        </h1>
                        <p className="hero-subtitle">
                            17 specialized AI agents that replicate a banker's brain, delivering
                            comprehensive sustainability assessments in under 15-30 minutes with
                            complete regulatory compliance.
                        </p>
                        <div className="hero-cta">
                            <button className="btn btn-white">Book a Demo</button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Trusted By Section */}
            <section className="section section-light trusted-section">
                <div className="container">
                    <p className="trusted-title">Trusted by leading financial institutions</p>
                    <div className="trusted-logos">
                        <span style={{ fontSize: '14px', color: '#5a616e' }}>EU Banks</span>
                        <span style={{ fontSize: '14px', color: '#5a616e' }}>Investment Firms</span>
                        <span style={{ fontSize: '14px', color: '#5a616e' }}>Asset Managers</span>
                        <span style={{ fontSize: '14px', color: '#5a616e' }}>Green Lenders</span>
                        <span style={{ fontSize: '14px', color: '#5a616e' }}>ESG Consultants</span>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="section section-light">
                <div className="container">
                    <div className="section-header">
                        <h2 className="section-title">Give your team superpowers</h2>
                        <p className="section-subtitle">
                            Automate tedious sustainability assessments and enable your team to focus on what they do best
                        </p>
                    </div>
                    <div className="features-grid">
                        <div className="feature-card">
                            <span className="feature-badge">AI-Powered Assessment</span>
                            <h3 className="feature-title">Automated Regulatory Coverage</h3>
                            <p className="feature-description">
                                Auto-sync with EU Taxonomy, CSRD, SFDR requirements. Evaluate sustainability
                                reports, green bond frameworks, and ESG disclosures within minutes.
                            </p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-badge">Real-time Analysis</span>
                            <h3 className="feature-title">AI-Generated Reports and Data Extraction</h3>
                            <p className="feature-description">
                                Let GreenGuard AI generate comprehensive assessment reports, extract key
                                sustainability metrics, and provide actionable insights with complete audit trails.
                            </p>
                        </div>
                        <div className="feature-card feature-card-blue">
                            <span className="feature-badge">17 AI Agents</span>
                            <h3 className="feature-title">Banker's Brain, Replicated</h3>
                            <p className="feature-description">
                                Our specialized AI agents work together to analyze KPIs, validate targets,
                                benchmark against peers, and assess regulatory compliance—just like an
                                experienced sustainability banker would.
                            </p>
                        </div>
                        <div className="feature-card">
                            <span className="feature-badge">Speed & Accuracy</span>
                            <h3 className="feature-title">15-30 Minute Assessments</h3>
                            <p className="feature-description">
                                What traditionally takes days or weeks is now completed in minutes.
                                Get comprehensive sustainability assessments without sacrificing accuracy or depth.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="how-it-works">
                <div className="container">
                    <div className="section-header">
                        <h2 className="section-title">How it works</h2>
                    </div>
                    <div className="how-it-works-grid">
                        <div className="how-it-works-card">
                            <div className="how-it-works-icon">
                                <UploadIcon />
                            </div>
                            <h4 className="how-it-works-title">Upload</h4>
                            <p className="how-it-works-description">
                                Upload sustainability reports, green bond frameworks, or ESG disclosures
                                from any data source—PDFs, annual reports, or direct integrations.
                            </p>
                        </div>
                        <div className="how-it-works-card">
                            <div className="how-it-works-icon">
                                <AnalyzeIcon />
                            </div>
                            <h4 className="how-it-works-title">Analyze</h4>
                            <p className="how-it-works-description">
                                GreenGuard's 17 AI agents analyze KPIs, validate green claims, benchmark
                                against peers, and check regulatory compliance automatically.
                            </p>
                        </div>
                        <div className="how-it-works-card">
                            <div className="how-it-works-icon">
                                <ReportIcon />
                            </div>
                            <h4 className="how-it-works-title">Report</h4>
                            <p className="how-it-works-description">
                                Receive comprehensive assessment reports with risk ratings, evidence
                                citations, recommendations, and full audit trails for compliance.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="stats-section">
                <div className="container">
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-number">17</div>
                            <div className="stat-label">Specialized AI Agents</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">15-30</div>
                            <div className="stat-label">Minutes per Assessment</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">100%</div>
                            <div className="stat-label">Regulatory Compliance</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">95%</div>
                            <div className="stat-label">Time Saved vs Manual</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* AI Agents Section */}
            <section id="agents" className="agents-section">
                <div className="container">
                    <div className="section-header">
                        <h2 className="section-title">Meet our AI Agents</h2>
                        <p className="section-subtitle">
                            17 specialized agents working together to deliver comprehensive sustainability assessments
                        </p>
                    </div>
                    <div className="agents-grid">
                        {agents.map((agent, index) => (
                            <div key={index} className="agent-card">
                                <AgentIcon>
                                    <span style={{ fontSize: '18px', fontWeight: '600' }}>{index + 1}</span>
                                </AgentIcon>
                                <h5 className="agent-name">{agent.name}</h5>
                                <p className="agent-description">{agent.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FAQ Section */}
            <section id="faq" className="faq-section">
                <div className="container">
                    <div className="faq-container">
                        <div className="faq-header">
                            <h2>Questions & Answers</h2>
                            <p>Learn more about what GreenGuard has to offer or feel free to contact us at hello@greenguard.ai</p>
                        </div>
                        <div className="faq-list">
                            {faqs.map((faq, index) => (
                                <div
                                    key={index}
                                    className={`faq-item ${openFaq === index ? 'active' : ''}`}
                                    onClick={() => toggleFaq(index)}
                                >
                                    <div className="faq-question">
                                        {faq.question}
                                        <span className="faq-icon"><PlusIcon /></span>
                                    </div>
                                    <div className="faq-answer">
                                        <p>{faq.answer}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section id="demo" className="cta-section">
                <div className="cta-container">
                    <h2 className="cta-title">Interested in testing GreenGuard?</h2>
                    <p className="cta-subtitle">
                        We welcome any interest in putting GreenGuard to the test. Submit your email
                        and we'll walk you through a demo and show you how GreenGuard can transform
                        your sustainability assessments.
                    </p>
                    <form className="cta-form" onSubmit={(e) => e.preventDefault()}>
                        <input
                            type="email"
                            className="cta-input"
                            placeholder="name@email.com"
                        />
                        <button type="submit" className="btn btn-white">Request Info</button>
                    </form>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <div className="footer-container">
                    <div className="footer-brand">
                        <img src="/logo.png" alt="GreenGuard" className="footer-logo" />
                        <span className="footer-brand-text">GreenGuard</span>
                    </div>
                    <div className="footer-center">
                        © 2025 GreenGuard. All Rights Reserved. | Have more questions? → <a href="mailto:hello@greenguard.ai">Get in touch</a>
                    </div>
                    <div className="footer-right">
                        <a href="#" className="footer-social">
                            <LinkedInIcon />
                        </a>
                    </div>
                </div>
            </footer>
        </div>
    )
}

export default App
