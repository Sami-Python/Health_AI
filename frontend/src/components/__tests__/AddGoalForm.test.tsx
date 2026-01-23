import '@testing-library/jest-dom'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AddGoalForm from '../AddGoalForm'
import { AuthProvider } from '@/context/AuthContext'

// Mock the AuthContext
jest.mock('@/context/AuthContext', () => ({
    useAuth: () => ({
        user: {
            uid: 'test-uid',
            getIdToken: async () => 'mock-token'
        },
        loading: false
    }),
    AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))

// Mock fetchWithRetry (utils)
jest.mock('@/lib/utils', () => ({
    fetchWithRetry: jest.fn(),
    API_BASE_URL: 'http://localhost:8000',
    cn: (...inputs: any[]) => JSON.stringify(inputs) // Simple mock to avoid crash
}))

// Mock toast
jest.mock('react-hot-toast', () => ({
    __esModule: true,
    default: {
        success: jest.fn(),
        error: jest.fn()
    }
}))

import { fetchWithRetry } from '@/lib/utils'

describe('AddGoalForm', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('renders the form correctly', () => {
        render(<AddGoalForm />)
        expect(screen.getByText('Create New Goal')).toBeInTheDocument()
        expect(screen.getByText(/Activity/i)).toBeInTheDocument()
    })

    it('submits data when form is filled', async () => {
        (fetchWithRetry as jest.Mock).mockResolvedValue({
            ok: true,
            json: async () => ({ status: 'success' })
        })

        render(<AddGoalForm />)

        // Select activity
        // Note: Default select might be tricky to test with simple getBy. 
        // Let's assume standard HTML select for MVP test, or just check the input.
        // Assuming AddGoalForm uses <select> or similar.

        const targetInput = screen.getByPlaceholderText(/e.g. 30/i)
        fireEvent.change(targetInput, { target: { value: '50' } })

        const submitBtn = screen.getByRole('button', { name: /Create Goal/i })
        fireEvent.click(submitBtn)

        // Wait for fetch to be called
        await waitFor(() => {
            expect(fetchWithRetry).toHaveBeenCalled()
        })
    })
})
