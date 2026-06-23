import { Component } from 'react'

/**
 * Top-level error boundary. Catches unhandled render errors so the whole
 * app does not go blank — shows a styled recovery screen instead.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] Uncaught render error:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ error: null })
    window.location.reload()
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-boundary-shell">
          <section className="panel error-boundary-panel">
            <div className="eyebrow">System Error</div>
            <h1>The console encountered an unexpected error</h1>
            <p className="panel-subtle">{this.state.error?.message || 'An unknown error occurred.'}</p>
            <button className="primary-button" onClick={this.handleReset}>
              Reload Console
            </button>
          </section>
        </div>
      )
    }
    return this.props.children
  }
}
