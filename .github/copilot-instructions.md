# AI Hackathon Use Cases - Copilot Instructions

## Project Overview
This is a multi-language AI hackathon repository with 5 production-ready civic AI systems. Each system is fully tested and designed for rapid hackathon extension.

## Critical Architecture Patterns

### Multi-Project Repository Structure
- **5 independent AI systems**: Each in its own directory with complete isolation
- **Python projects**: Emergency-Response-Agent, Policy-Compliance-Checker, Virtual-Citizen-Assistant, Document-Eligibility-Agent
- **.NET project**: DotNet-Virtual-Citizen-Assistant (separate tech stack)
- **Common pattern**: Each project has `src/`, `tests/`, `assets/`, `requirements.txt`, `README.md`, `run_all_tests.py`

### Semantic Kernel Integration (Critical Version Requirements)
- **Must use semantic-kernel==1.37.0** (all Python projects upgraded from broken 0.9.1b1)
- **Plugin pattern**: Use `@kernel_function` decorator with `typing.Annotated` parameters
- **Import path**: `from semantic_kernel.functions import kernel_function`
- **Parameter annotation**: `query: Annotated[str, "Description"]` instead of old `@sk_function_context_parameter`

```python
# CORRECT modern pattern (v1.37.0+)
from semantic_kernel.functions import kernel_function
from typing import Annotated

@kernel_function(description="Function description", name="function_name")
def my_function(self, param: Annotated[str, "Parameter description"]) -> str:
    return result
```

### Testing Architecture
- **Validation workflow**: Always run `python run_all_tests.py` in each project directory
- **Test hierarchy**: setup → core components → plugins → integration
- **100% test coverage mandate**: All projects have comprehensive test suites (59-83 tests each)
- **Test patterns**: pytest with async support, mock services for offline development

### Azure AI Services Integration
- **Configuration pattern**: Environment variables via `.env` files, fallback to mock services
- **Required services**: Azure OpenAI, Document Intelligence, AI Search, Graph API
- **Mock fallbacks**: All projects work without API keys for development
- **Service initialization**: Always check for API key availability before real service calls

### Dependencies and Compatibility
- **Python version**: 3.8+ minimum, 3.9+ preferred
- **Critical upgrades applied**: PyPDF2 → pypdf, deprecated dependencies removed
- **Azure SDK versions**: Latest stable releases (check requirements.txt for exact versions)
- **Testing stack**: pytest + pytest-asyncio + pytest-mock + pytest-cov

## Development Workflow

### Quick Start Pattern
1. Navigate to specific project: `cd [Project-Name]/`
2. Install dependencies: `pip install -r requirements.txt`
3. Validate setup: `python run_all_tests.py`
4. Run demo: `python demo.py` (if available)
5. Start development: `python src/main.py`

### Plugin Development (.NET vs Python)
**Python projects**: Use semantic-kernel with `@kernel_function` decorator
**DotNet project**: Use `[KernelFunction, Description("...")]` attribute pattern

### Configuration Management
- **Environment variables**: Check for API keys, graceful degradation to mocks
- **Settings pattern**: Centralized config classes with validation
- **Asset management**: Sample data in `assets/` directories for testing

## Project-Specific Knowledge

### Emergency-Response-Agent
- **Multi-agent coordination**: Weather service + response planning + resource allocation
- **Weather API**: OpenWeatherMap integration with intelligent fallbacks
- **Data models**: 15+ Pydantic models for emergency scenarios

### Policy-Compliance-Checker  
- **Document processing**: pypdf for PDF handling, python-docx for Word docs
- **AI analysis**: Multi-step compliance checking with rule engine
- **Plugin system**: PolicyAnalysisPlugin + PolicyImprovementPlugin

### Virtual-Citizen-Assistant
- **RAG implementation**: Azure AI Search + document retrieval + chat interface
- **Plugin architecture**: DocumentRetrievalPlugin + SchedulingPlugin
- **Search patterns**: Semantic + keyword + category-based filtering

### Document-Eligibility-Agent
- **Email processing**: Microsoft Graph API integration
- **Document intelligence**: Azure Form Recognizer for OCR
- **Classification**: AI-powered document type detection

### DotNet-Virtual-Citizen-Assistant
- **Modern .NET stack**: .NET 9 + Semantic Kernel + Bootstrap 5
- **MVC pattern**: Controllers + Views + Services + Plugins architecture
- **Testing framework**: xUnit + FluentAssertions + Moq

## Critical Do's and Don'ts

### DO
- Always validate with `run_all_tests.py` after changes
- Use modern `@kernel_function` decorator syntax
- Check existing mock services before adding external dependencies
- Follow the established src/tests/assets directory structure
- Use the project's existing error handling patterns

### DON'T  
- Use deprecated PyPDF2 or old semantic-kernel versions
- Skip running tests - all projects are designed for 100% pass rate
- Add external API dependencies without fallback mechanisms
- Mix Python and .NET project patterns
- Modify shared dependencies without testing all affected projects

## Extension Points for Hackathon Teams
- **New emergency scenarios** in Emergency-Response-Agent
- **Additional document types** in Policy-Compliance-Checker
- **Custom plugins** following the established patterns
- **UI enhancements** using existing frontend frameworks
- **API integrations** with proper mock fallbacks