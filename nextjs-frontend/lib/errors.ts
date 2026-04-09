/**
 * Safely extracts a string error message from various API error formats.
 * Handles FastAPI/Pydantic validation errors, plain objects, and strings.
 */
export function extractErrorMessage(error: any): string {
  // If already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // Handle Pydantic validation error array
  if (error?.detail && Array.isArray(error.detail)) {
    const messages = error.detail.map((err: any) => {
      if (typeof err === 'string') return err;
      if (err.msg) return err.msg;
      return JSON.stringify(err);
    });
    return messages.join(', ');
  }

  // Handle single validation error object
  if (error?.type && error?.msg) {
    return error.msg;
  }

  // Try common error properties
  if (error?.message && typeof error.message === 'string') {
    return error.message;
  }

  if (error?.detail && typeof error.detail === 'string') {
    return error.detail;
  }

  if (error?.error && typeof error.error === 'string') {
    return error.error;
  }

  // Last resort: stringify the object
  try {
    return JSON.stringify(error);
  } catch {
    return 'An unknown error occurred';
  }
}

/**
 * Extracts error message from a fetch response.
 */
export async function extractResponseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return extractErrorMessage(data);
  } catch {
    return `HTTP ${response.status}: ${response.statusText}`;
  }
}
