"""
Emergency Response Agent - Integrated Multi-Agent Web Application
Flask-based web interface for the integrated AI agent ecosystem.
"""
import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add other agent directories to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir / "Policy-Compliance-Checker" / "src"))
sys.path.append(str(root_dir / "Virtual-Citizen-Assistant" / "src"))
sys.path.append(str(root_dir / "Document-Eligibility-Agent" / "src"))

from src.models.emergency_models import (
    EmergencyScenario, EmergencyType, SeverityLevel, ResponsePhase
)
from src.orchestration.emergency_coordinator import EmergencyResponseCoordinator

# Import other AI agents with error handling
policy_checker_available = False
citizen_assistant_available = False
document_agent_available = False

try:
    sys.path.append(str(root_dir / "Policy-Compliance-Checker" / "src"))
    from main import PolicyComplianceChecker
    policy_checker_available = True
    print("✓ Policy Compliance Checker imported successfully")
except Exception as e:
    print(f"⚠ Policy Compliance Checker not available: {e}")
    PolicyComplianceChecker = None

try:
    sys.path.append(str(root_dir / "Virtual-Citizen-Assistant" / "src"))
    from main import VirtualCitizenAssistant
    citizen_assistant_available = True
    print("✓ Virtual Citizen Assistant imported successfully")
except Exception as e:
    print(f"⚠ Virtual Citizen Assistant not available: {e}")
    VirtualCitizenAssistant = None

try:
    sys.path.append(str(root_dir / "Document-Eligibility-Agent" / "src"))
    from main import DocumentEligibilityAgent
    document_agent_available = True
    print("✓ Document Eligibility Agent imported successfully")
except Exception as e:
    print(f"⚠ Document Eligibility Agent not available: {e}")
    DocumentEligibilityAgent = None

app = Flask(__name__)
app.secret_key = 'emergency_response_secret_key_2025'

# Global agent instances
coordinator = None
policy_checker = None
citizen_assistant = None
document_agent = None

class IntegratedAgentManager:
    """Manager for all AI agents in the integrated system"""
    
    def __init__(self):
        self.coordinator = None
        self.policy_checker = None
        self.citizen_assistant = None
        self.document_agent = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all available AI agents"""
        try:
            # Initialize Emergency Response Coordinator
            self.coordinator = EmergencyResponseCoordinator()
            await self.coordinator.initialize()
            print("✓ Emergency Response Coordinator initialized")
            
            # Initialize Policy Compliance Checker
            if PolicyComplianceChecker and policy_checker_available:
                self.policy_checker = PolicyComplianceChecker(
                    azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY")
                )
                await self.policy_checker.initialize()
                print("✓ Policy Compliance Checker initialized")
            
            # Initialize Virtual Citizen Assistant
            if VirtualCitizenAssistant and citizen_assistant_available:
                self.citizen_assistant = VirtualCitizenAssistant()
                await self.citizen_assistant.initialize()
                print("✓ Virtual Citizen Assistant initialized")
            
            # Initialize Document Eligibility Agent
            if DocumentEligibilityAgent and document_agent_available:
                self.document_agent = DocumentEligibilityAgent(use_mock_services=True)
                await self.document_agent.initialize()
                print("✓ Document Eligibility Agent initialized")
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing agents: {e}")
            # Fallback to just the emergency coordinator
            try:
                self.coordinator = EmergencyResponseCoordinator()
                await self.coordinator.initialize()
                print("✓ Emergency Response Coordinator initialized (fallback mode)")
                self.initialized = True
                return True
            except Exception as fallback_error:
                print(f"Critical error: {fallback_error}")
                return False

# Global agent manager
agent_manager = IntegratedAgentManager()

def get_coordinator():
    """Get or create the emergency coordinator instance."""
    if agent_manager.coordinator is None:
        agent_manager.coordinator = EmergencyResponseCoordinator()
    return agent_manager.coordinator

def get_agent_manager():
    """Get the integrated agent manager instance."""
    return agent_manager
    return coordinator

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Emergency response dashboard."""
    return render_template('dashboard.html')

@app.route('/create_scenario')
def create_scenario():
    """Create new emergency scenario page."""
    emergency_types = [e.value for e in EmergencyType]
    severity_levels = [e.value for e in SeverityLevel]
    return render_template('create_scenario.html', 
                         emergency_types=emergency_types,
                         severity_levels=severity_levels)

@app.route('/api/scenarios', methods=['POST'])
def api_create_scenario():
    """API endpoint to create and process emergency scenario."""
    try:
        data = request.get_json()
        
        # Create emergency scenario
        scenario = EmergencyScenario(
            scenario_id=data.get('scenario_id', f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            incident_type=EmergencyType(data['incident_type']),
            severity_level=SeverityLevel(int(data['severity_level'])),
            location=data['location'],
            affected_area_radius=float(data['affected_area_radius']),
            estimated_population_affected=int(data['estimated_population_affected']),
            duration_hours=int(data.get('duration_hours', 24)),
            description=data.get('description', ''),
            special_conditions=data.get('special_conditions', [])
        )
        
        # Process scenario with coordinator
        coord = get_coordinator()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response_plan = loop.run_until_complete(coord.coordinate_response(scenario))
        finally:
            loop.close()
        
        # Convert response plan to dict for JSON serialization
        plan_dict = {
            'plan_id': response_plan.plan_id,
            'scenario_id': response_plan.scenario_id,
            'lead_agency': response_plan.lead_agency,
            'supporting_agencies': response_plan.supporting_agencies,
            'activation_time': response_plan.activation_time.isoformat(),
            'estimated_duration': str(response_plan.estimated_duration),
            'immediate_actions': response_plan.immediate_actions,
            'resource_allocation': {
                'personnel_deployment': response_plan.resource_allocation.personnel_deployment,
                'equipment_requirements': response_plan.resource_allocation.equipment_requirements,
                'facility_assignments': response_plan.resource_allocation.facility_assignments
            },
            'timeline_milestones': [
                {
                    'milestone_name': m.milestone_name,
                    'estimated_time': m.estimated_time.isoformat(),
                    'responsible_agency': m.responsible_agency,
                    'description': m.description
                } for m in response_plan.timeline_milestones
            ],
            'communication_plan': response_plan.communication_plan
        }
        
        return jsonify({
            'success': True,
            'scenario': {
                'scenario_id': scenario.scenario_id,
                'incident_type': scenario.incident_type.value,
                'severity_level': scenario.severity_level.value,
                'location': scenario.location,
                'affected_area_radius': scenario.affected_area_radius,
                'estimated_population_affected': scenario.estimated_population_affected,
                'duration_hours': scenario.duration_hours,
                'description': scenario.description
            },
            'response_plan': plan_dict
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/weather/<lat>/<lon>')
def api_get_weather(lat, lon):
    """API endpoint to get weather data for coordinates."""
    try:
        coord = get_coordinator()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            weather_data = loop.run_until_complete(
                coord.weather_service.get_current_conditions(float(lat), float(lon))
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'weather': {
                'temperature': weather_data.temperature,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'pressure': weather_data.pressure,
                'visibility': weather_data.visibility,
                'conditions': weather_data.conditions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/scenarios')
def scenarios():
    """View existing scenarios."""
    return render_template('scenarios.html')

@app.route('/plan/<plan_id>')
def view_plan(plan_id):
    """View specific response plan."""
    return render_template('plan_detail.html', plan_id=plan_id)

@app.route('/map')
def map_view():
    """Interactive map view."""
    return render_template('map.html')

@app.route('/reports')
def reports():
    """Reports and analytics page."""
    return render_template('reports.html')

# ========== INTEGRATED AI AGENTS ROUTES ==========

@app.route('/agents')
def agents_hub():
    """Main hub for all AI agents."""
    manager = get_agent_manager()
    agent_status = {
        'emergency_response': manager.coordinator is not None,
        'policy_compliance': manager.policy_checker is not None,
        'citizen_assistant': manager.citizen_assistant is not None,
        'document_eligibility': manager.document_agent is not None
    }
    return render_template('agents_hub.html', agent_status=agent_status)

# Policy Compliance Checker Routes
@app.route('/policy-compliance')
def policy_compliance():
    """Policy compliance checker interface."""
    return render_template('policy_compliance.html')

@app.route('/api/policy/analyze', methods=['POST'])
def api_policy_analyze():
    """API endpoint for policy analysis."""
    try:
        manager = get_agent_manager()
        if not manager.policy_checker:
            return jsonify({
                'success': False,
                'error': 'Policy Compliance Checker not available'
            }), 503
        
        data = request.get_json()
        document_path = data.get('document_path')
        policy_text = data.get('policy_text')
        
        if not document_path and not policy_text:
            return jsonify({
                'success': False,
                'error': 'Either document_path or policy_text required'
            }), 400
        
        # Run policy analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if document_path:
                result = loop.run_until_complete(
                    manager.policy_checker.analyze_document(document_path)
                )
            else:
                result = loop.run_until_complete(
                    manager.policy_checker.analyze_policy_text(policy_text)
                )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Virtual Citizen Assistant Routes
@app.route('/citizen-assistant')
def citizen_assistant():
    """Virtual citizen assistant interface."""
    return render_template('citizen_assistant.html')

@app.route('/api/citizen/chat', methods=['POST'])
def api_citizen_chat():
    """API endpoint for citizen assistant chat."""
    try:
        manager = get_agent_manager()
        if not manager.citizen_assistant:
            return jsonify({
                'success': False,
                'error': 'Virtual Citizen Assistant not available'
            }), 503
        
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message required'
            }), 400
        
        # Run citizen assistant chat
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(
                manager.citizen_assistant.chat(message)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Document Eligibility Agent Routes
@app.route('/document-eligibility')
def document_eligibility():
    """Document eligibility agent interface."""
    return render_template('document_eligibility.html')

@app.route('/api/document/process', methods=['POST'])
def api_document_process():
    """API endpoint for document processing."""
    try:
        manager = get_agent_manager()
        if not manager.document_agent:
            return jsonify({
                'success': False,
                'error': 'Document Eligibility Agent not available'
            }), 503
        
        data = request.get_json()
        document_type = data.get('document_type')
        document_content = data.get('document_content')
        applicant_info = data.get('applicant_info', {})
        
        if not document_type or not document_content:
            return jsonify({
                'success': False,
                'error': 'Document type and content required'
            }), 400
        
        # Run document processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                manager.document_agent.process_document(
                    document_type, document_content, applicant_info
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Cross-Agent Collaboration Routes
@app.route('/api/agents/collaborate', methods=['POST'])
def api_agents_collaborate():
    """API endpoint for cross-agent collaboration."""
    try:
        manager = get_agent_manager()
        data = request.get_json()
        
        task_type = data.get('task_type')
        task_data = data.get('task_data', {})
        
        if task_type == 'emergency_policy_check':
            # Emergency scenario with policy compliance check
            scenario_data = task_data.get('scenario')
            policy_documents = task_data.get('policies', [])
            
            # Create emergency scenario
            scenario_result = None
            if manager.coordinator:
                scenario = EmergencyScenario(
                    incident_type=EmergencyType(scenario_data['incident_type']),
                    severity_level=SeverityLevel(scenario_data['severity_level']),
                    location=scenario_data['location'],
                    description=scenario_data['description']
                )
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    response_plan = loop.run_until_complete(
                        manager.coordinator.coordinate_response(scenario)
                    )
                    scenario_result = {
                        'plan_id': response_plan.plan_id,
                        'lead_agency': response_plan.lead_agency,
                        'immediate_actions': response_plan.immediate_actions
                    }
                finally:
                    loop.close()
            
            # Check policies for compliance
            policy_results = []
            if manager.policy_checker and policy_documents:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    for policy in policy_documents:
                        result = loop.run_until_complete(
                            manager.policy_checker.analyze_policy_text(policy)
                        )
                        policy_results.append(result)
                finally:
                    loop.close()
            
            return jsonify({
                'success': True,
                'emergency_response': scenario_result,
                'policy_compliance': policy_results,
                'collaboration_summary': 'Emergency response plan generated with policy compliance validation'
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown task type: {task_type}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Agent Status and Health Check
@app.route('/api/agents/status')
def api_agents_status():
    """Get status of all agents."""
    manager = get_agent_manager()
    return jsonify({
        'emergency_response': {
            'available': manager.coordinator is not None,
            'status': 'active' if manager.coordinator else 'unavailable'
        },
        'policy_compliance': {
            'available': manager.policy_checker is not None,
            'status': 'active' if manager.policy_checker else 'unavailable'
        },
        'citizen_assistant': {
            'available': manager.citizen_assistant is not None,
            'status': 'active' if manager.citizen_assistant else 'unavailable'
        },
        'document_eligibility': {
            'available': manager.document_agent is not None,
            'status': 'active' if manager.document_agent else 'unavailable'
        },
        'system_status': 'operational' if manager.initialized else 'initializing'
    })

if __name__ == '__main__':
    # Initialize all agents on startup
    print("🚀 Starting Integrated AI Agent System...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(agent_manager.initialize())
        if success:
            print("✅ All available agents initialized successfully!")
            print("🌐 Starting web application...")
        else:
            print("⚠️  Some agents failed to initialize, running in limited mode")
    except Exception as e:
        print(f"❌ Critical error during initialization: {e}")
        print("🔄 Starting with emergency response agent only...")
    finally:
        loop.close()
    
    app.run(debug=True, host='0.0.0.0', port=5000)