import { useState } from 'react'
import {
  Box,
  TextField,
  Button,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Paper,
  Alert,
  SelectChangeEvent,
  Card,
  CardContent,
  CircularProgress,
  Container,
} from '@mui/material'

import { parseMarkdown } from './utils/markDownParser.js'

interface StartupForm {
  company_name: string
  industry: string
  stage: string
  funding_needed: number
  minimum_investment: number
  equity_offering: number
  funding_timeline: string
  primary_use: string
  description: string
}

interface StreamResponse {
  type: 'token' | 'end' | 'error'
  content: string
}

const INDUSTRY_OPTIONS = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'E-commerce',
  'AI/ML',
  'Clean Energy',
  'Other'
]

const STAGE_OPTIONS = ['Idea', 'Early Stage', 'Growth', 'Scale']

const TIMELINE_OPTIONS = [
  '0-3 months',
  '3-6 months',
  '6-12 months',
  '12+ months'
]

const PRIMARY_USE_OPTIONS = [
  'Product Development',
  'Team Growth',
  'Marketing & Sales',
  'Operations',
  'Research & Development',
  'Market Expansion',
  'Working Capital',
  'Other'
]

function App() {
  const [formData, setFormData] = useState<Partial<StartupForm>>({})
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [streamingText, setStreamingText] = useState<string>('')
  const [streamComplete, setStreamComplete] = useState(false)
  const [showForm, setShowForm] = useState(true)
  const [hasResults, setHasResults] = useState(false)

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : '') : value,
    }))
  }

  const handleSelectChange = (e: SelectChangeEvent) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setStreamingText('')
    setStreamComplete(false)
    setShowForm(false)

    try {
      const response = await fetch('http://127.0.0.1:8000/findRelatedStartups', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Failed to initialize stream reader')
      }

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: StreamResponse = JSON.parse(line.slice(6))
              
              if (data.type === 'token') {
                setStreamingText(prev => prev + data.content)
              } else if (data.type === 'error') {
                setError(data.content)
                break
              } else if (data.type === 'end') {
                setStreamComplete(true)
                setHasResults(true)
                break
              }
            } catch (err) {
              console.error('Error parsing chunk:', err)
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Error:', err)
      setError(err.message || 'Failed to submit. Please try again.')
      setShowForm(true)
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    setShowForm(true)
  }

  const handleViewResults = () => {
    setShowForm(false)
  }

  // Parse the markdown and create HTML
  const formattedContent = streamingText ? parseMarkdown(streamingText) : ''

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {showForm ? (
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4" component="h1" color="primary">
              Find Startup Investors
            </Typography>
            {hasResults && (
              <Button
                variant="contained"
                onClick={handleViewResults}
                color="primary"
              >
                View Previous Results
              </Button>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="primary" gutterBottom>
                  Company Information
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Company Name"
                  name="company_name"
                  value={formData.company_name || ''}
                  onChange={handleTextChange}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Industry</InputLabel>
                  <Select
                    name="industry"
                    value={formData.industry || ''}
                    onChange={handleSelectChange}
                    label="Industry"
                  >
                    {INDUSTRY_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Stage</InputLabel>
                  <Select
                    name="stage"
                    value={formData.stage || ''}
                    onChange={handleSelectChange}
                    label="Stage"
                  >
                    {STAGE_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Investment Details
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Funding Needed"
                  name="funding_needed"
                  type="number"
                  value={formData.funding_needed || ''}
                  onChange={handleTextChange}
                  InputProps={{
                    startAdornment: (
                      <Typography variant="body1" sx={{ color: 'text.secondary', mr: 1 }}>
                        $
                      </Typography>
                    ),
                  }}
                  placeholder="Enter total amount needed"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Minimum Investment"
                  name="minimum_investment"
                  type="number"
                  value={formData.minimum_investment || ''}
                  onChange={handleTextChange}
                  InputProps={{
                    startAdornment: (
                      <Typography variant="body1" sx={{ color: 'text.secondary', mr: 1 }}>
                        $
                      </Typography>
                    ),
                  }}
                  placeholder="Minimum investment"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  label="Equity Offering"
                  name="equity_offering"
                  type="number"
                  value={formData.equity_offering || ''}
                  onChange={handleTextChange}
                  InputProps={{
                    endAdornment: (
                      <Typography variant="body1" sx={{ color: 'text.secondary', ml: 1 }}>
                        %
                      </Typography>
                    ),
                  }}
                  placeholder="Enter percentage"
                  inputProps={{ min: 0, max: 100 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Funding Timeline</InputLabel>
                  <Select
                    name="funding_timeline"
                    value={formData.funding_timeline || ''}
                    onChange={handleSelectChange}
                    label="Funding Timeline"
                  >
                    {TIMELINE_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth required>
                  <InputLabel>Primary Use of Funds</InputLabel>
                  <Select
                    name="primary_use"
                    value={formData.primary_use || ''}
                    onChange={handleSelectChange}
                    label="Primary Use of Funds"
                  >
                    {PRIMARY_USE_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Additional Information
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Description"
                  name="description"
                  multiline
                  rows={4}
                  value={formData.description || ''}
                  onChange={handleTextChange}
                  placeholder="Describe your business, market opportunity, and how you plan to use the funds"
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  size="large"
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Find Investors'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      ) : (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={handleBack}
              sx={{ mb: 2 }}
            >
              Back to Form
            </Button>
            <Typography variant="h5" component="h2" color="primary" sx={{ flex: 1 }}>
              Investor's Recommendation
            </Typography>
          </Box>

          <Paper elevation={3} sx={{ p: 4 }}>
            {loading && !streamComplete && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                <CircularProgress />
              </Box>
            )}

            <Card>
              <CardContent>
                <Box
                  className="markdown-content"
                  sx={{
                    '& p': { mb: 2 },
                    '& ul, & ol': { mb: 2, pl: 3 },
                  }}
                  dangerouslySetInnerHTML={{ __html: formattedContent || 'Generating response...' }}
                />
              </CardContent>
            </Card>

            {streamComplete && (
              <Alert severity="success" sx={{ mt: 3 }}>
                Analysis complete!
              </Alert>
            )}
          </Paper>
        </Box>
      )}
    </Container>
  )
}

export default App
