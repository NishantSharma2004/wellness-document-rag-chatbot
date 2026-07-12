class ChatbotException(Exception):
    """Base exception for Wellness Chatbot"""
    pass

class LoaderException(ChatbotException):
    """Error during document loading"""
    pass

class CleanException(ChatbotException):
    """Error during document cleaning"""
    pass

class ChunkException(ChatbotException):
    """Error during chunking"""
    pass

class IndexException(ChatbotException):
    """Error during index creation or management"""
    pass

class RetrievalException(ChatbotException):
    """Error during hybrid retrieval"""
    pass

class GenerationException(ChatbotException):
    """Error during response generation"""
    pass

class SafetyException(ChatbotException):
    """Error during safety validation"""
    pass

class CitationValidationError(GenerationException):
    """Error during citation validation"""
    pass
