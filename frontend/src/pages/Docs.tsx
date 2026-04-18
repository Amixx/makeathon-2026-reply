import { Link } from "react-router";
import { installSnippets, mcpSections, mcpToolGroups } from "../lib/mcpDocs";
import styles from "./Docs.module.css";

const totalTools = mcpToolGroups.reduce((sum, group) => sum + group.tools.length, 0);

function CodeBlock({
  label,
  language,
  content,
}: {
  label: string;
  language: string;
  content: string;
}) {
  return (
    <div className={styles.codeBlock}>
      <div className={styles.codeHeader}>
        <span>{label}</span>
        <span>{language}</span>
      </div>
      <pre>
        <code>{content}</code>
      </pre>
    </div>
  );
}

export default function Docs() {
  return (
    <main className={styles.page}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarCard}>
          <p className={styles.sidebarEyebrow}>Documentation</p>
          <h1 className={styles.sidebarTitle}>Campus Co-Pilot MCP</h1>
          <p className={styles.sidebarText}>
            Tool docs for the TUM campus integration layer that powers the agent.
          </p>
        </div>

        <nav className={styles.sidebarNav} aria-label="Sections">
          {mcpSections.map((section) => (
            <a key={section.id} href={`#${section.id}`} className={styles.sidebarLink}>
              {section.label}
            </a>
          ))}
          <a href="#tool-reference" className={styles.sidebarLink}>
            Tool Reference
          </a>
        </nav>
      </aside>

      <div className={styles.content}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>MCP Docs</p>
            <h1>Use Campus Co-Pilot&apos;s MCP server</h1>
            <p className={styles.heroText}>
              Campus Co-Pilot turns TUM systems into a single MCP surface for discovery,
              planning, and action. It can retrieve public campus data, reuse TUM SSO
              sessions, and stage real-world operations like course and sports registration.
            </p>
            <div className={styles.heroActions}>
              <a href="#quickstart" className={styles.primaryAction}>
                Start with Quickstart
              </a>
              <Link to="/chat" className={styles.secondaryAction}>
                Open the app
              </Link>
            </div>
          </div>

          <div className={styles.heroPanel}>
            <div className={styles.statGrid}>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{totalTools}</span>
                <span className={styles.statLabel}>Live tools</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>12</span>
                <span className={styles.statLabel}>Tool groups</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>/mcp</span>
                <span className={styles.statLabel}>Public endpoint</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>SSO</span>
                <span className={styles.statLabel}>Playwright auth</span>
              </div>
            </div>

            <CodeBlock
              label="Remote endpoint"
              language="bash"
              content={"codex mcp add campus-copilot --url https://<your-host>/mcp"}
            />
          </div>
        </section>

        <section className={styles.installSection}>
          <div className={styles.sectionHeader}>
            <p className={styles.sectionKicker}>Install</p>
            <h2>Connect the MCP to your tools</h2>
            <p>
              Use the deployed streamable HTTP endpoint directly from your coding agent or
              MCP-capable client.
            </p>
          </div>

          <div className={styles.installGrid}>
            {installSnippets.map((snippet) => (
              <article key={snippet.title} className={styles.installCard}>
                <h3>{snippet.title}</h3>
                <p>{snippet.description}</p>
                <CodeBlock
                  label={snippet.title}
                  language="text"
                  content={snippet.code}
                />
              </article>
            ))}
          </div>
        </section>

        {mcpSections.map((section) => (
          <section key={section.id} id={section.id} className={styles.section}>
            <div className={styles.sectionHeader}>
              {section.eyebrow ? <p className={styles.sectionKicker}>{section.eyebrow}</p> : null}
              <h2>{section.title}</h2>
              <p>{section.intro}</p>
            </div>

            <div className={styles.sectionBody}>
              {section.body?.map((paragraph) => (
                <p key={paragraph} className={styles.bodyText}>
                  {paragraph}
                </p>
              ))}

              {section.bullets ? (
                <ul className={styles.bulletList}>
                  {section.bullets.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}

              {section.code ? (
                <CodeBlock
                  label={section.code.label}
                  language={section.code.language}
                  content={section.code.content}
                />
              ) : null}

              {section.callout ? <div className={styles.callout}>{section.callout}</div> : null}
            </div>
          </section>
        ))}

        <section id="tool-reference" className={styles.section}>
          <div className={styles.sectionHeader}>
            <p className={styles.sectionKicker}>Reference</p>
            <h2>Tool reference</h2>
            <p>
              The current server registers {totalTools} tools. Modules are grouped here the
              same way they are registered in the backend, so the docs line up with the
              actual MCP surface area.
            </p>
          </div>

          <div className={styles.referenceList}>
            {mcpToolGroups.map((group) => (
              <article key={group.slug} className={styles.referenceCard}>
                <div className={styles.referenceHeader}>
                  <div>
                    <h3>{group.title}</h3>
                    <p>{group.summary}</p>
                  </div>
                  <span className={styles.referenceCount}>{group.tools.length} tools</span>
                </div>

                <div className={styles.toolTable}>
                  {group.tools.map((tool) => (
                    <div key={tool.name} className={styles.toolRow}>
                      <code>{tool.name}</code>
                      <p>{tool.description}</p>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
