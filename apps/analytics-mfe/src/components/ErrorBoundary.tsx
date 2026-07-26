import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Alert, AlertTitle, Box, Button } from '@mui/material'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  error: Error | null
}

/**
 * Prevents a single screen crash from blanking the whole microfrontend
 * (STATE-ERROR). The parent gives this a `key` per route so a new screen
 * remounts a fresh boundary instead of inheriting a stale error.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('NovaSteel analytics screen error', error, info)
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <Box sx={{ p: 2 }}>
          <Alert
            severity="error"
            role="alert"
            action={
              <Button color="inherit" size="small" onClick={() => this.setState({ error: null })}>
                Retry
              </Button>
            }
          >
            <AlertTitle>This view could not be rendered</AlertTitle>
            {this.state.error.message}
          </Alert>
        </Box>
      )
    }
    return this.props.children
  }
}
