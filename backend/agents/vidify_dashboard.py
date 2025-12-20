"""Vidify Dashboard Agent - Manages Vidify HQ Dashboard via natural language.

This agent handles all Vidify HQ dashboard operations:
- Client management (add, list, search)
- Project management (add, list, update)
- Transaction tracking (income, expenses)
- Team management (add members, pay salaries)
- Dashboard statistics
"""
import logging
from typing import Dict, Any, Optional
from clients.firebase_client import firebase_client
from config import settings

logger = logging.getLogger(__name__)


class VidifyDashboardAgent:
    """Agent for managing Vidify HQ Dashboard through natural language commands."""
    
    def __init__(self):
        """Initialize Vidify Dashboard Agent."""
        self.firebase = firebase_client
        self.owner_name = settings.owner_name
        logger.info("🎬 Vidify Dashboard Agent initialized")
    
    @property
    def is_connected(self) -> bool:
        """Check if Firebase is connected."""
        return self.firebase.is_connected
    
    async def handle_intent(
        self,
        intent: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route intent to appropriate handler.
        
        Args:
            intent: The detected intent
            parameters: Extracted parameters
            
        Returns:
            Dict with response and result
        """
        if not self.is_connected:
            return {
                "success": False,
                "response": f"Sorry {self.owner_name}, I can't connect to Vidify HQ right now. Please check the Firebase configuration."
            }
        
        handlers = {
            "vidify_add_client": self.add_client,
            "vidify_add_project": self.add_project,
            "vidify_log_income": self.log_income,
            "vidify_log_expense": self.log_expense,
            "vidify_add_team_member": self.add_team_member,
            "vidify_pay_salary": self.pay_salary,
            "vidify_get_stats": self.get_stats,
            "vidify_list_clients": self.list_clients,
            "vidify_list_projects": self.list_projects,
        }
        
        handler = handlers.get(intent)
        if handler:
            return await handler(parameters)
        
        return {
            "success": False,
            "response": f"I don't know how to handle '{intent}' for Vidify, {self.owner_name}."
        }
    
    # ==================== CLIENT OPERATIONS ====================
    
    async def add_client(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new client to Vidify HQ.
        
        Example prompts:
        - "Add client Ahmad Khan to Vidify"
        - "Add new client ABC Company"
        """
        name = params.get("name") or params.get("client_name")
        email = params.get("email", "")
        company = params.get("company", "")
        
        if not name:
            return {
                "success": False,
                "response": f"What's the client's name, {self.owner_name}?"
            }
        
        result = await self.firebase.add_client(
            name=name,
            email=email,
            company=company
        )
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"✅ Added **{name}** to Vidify HQ clients, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't add client: {result.get('error')}"
            }
    
    async def list_clients(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all clients.
        
        Example prompts:
        - "Show Vidify clients"
        - "List all clients in Vidify"
        """
        status = params.get("status")  # Optional: "active" or "inactive"
        
        clients = await self.firebase.get_clients(status=status)
        
        if not clients:
            return {
                "success": True,
                "response": f"No clients found in Vidify HQ, {self.owner_name}."
            }
        
        client_list = "\n".join([
            f"• **{c.get('name')}** ({c.get('company', 'No company')}) - Paid: Rs {c.get('totalPaid', 0):,.0f}"
            for c in clients[:10]  # Limit to 10
        ])
        
        return {
            "success": True,
            "response": f"📋 **Vidify HQ Clients** ({len(clients)} total):\n\n{client_list}",
            "data": {"clients": clients}
        }
    
    # ==================== PROJECT OPERATIONS ====================
    
    async def add_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new project.
        
        Example prompts:
        - "Create project Website Design for Ahmad, total 50000"
        - "Add project for ABC Company - App Development $5000"
        """
        name = params.get("name") or params.get("project_name")
        client_name = params.get("client_name") or params.get("client")
        amount = params.get("amount", 0) or params.get("total_amount", 0)
        
        if not name:
            return {
                "success": False,
                "response": f"What should I call this project, {self.owner_name}?"
            }
        
        # Find client by name
        client = None
        if client_name:
            client = await self.firebase.find_client_by_name(client_name)
        
        if client_name and not client:
            # Create client if not found
            client_result = await self.firebase.add_client(name=client_name)
            if client_result.get("success"):
                client_id = client_result["id"]
                logger.info(f"Created new client '{client_name}' for project")
            else:
                return {
                    "success": False,
                    "response": f"❌ Couldn't find or create client '{client_name}'"
                }
        else:
            client_id = client.get("id") if client else None
        
        if not client_id:
            return {
                "success": False,
                "response": f"Which client is this project for, {self.owner_name}?"
            }
        
        result = await self.firebase.add_project(
            name=name,
            client_id=client_id,
            total_amount=float(amount) if amount else 0
        )
        
        if result.get("success"):
            amount_text = f" (Rs {amount:,.0f})" if amount else ""
            return {
                "success": True,
                "response": f"✅ Created project **{name}**{amount_text} for **{client_name or 'client'}**, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't create project: {result.get('error')}"
            }
    
    async def list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all projects.
        
        Example prompts:
        - "Show Vidify projects"
        - "List active projects"
        """
        status = params.get("status")
        
        projects = await self.firebase.get_projects(status=status)
        
        if not projects:
            return {
                "success": True,
                "response": f"No projects found in Vidify HQ, {self.owner_name}."
            }
        
        project_list = "\n".join([
            f"• **{p.get('name')}** - {p.get('status', 'Unknown')} (Paid: Rs {p.get('paidAmount', 0):,.0f}/{p.get('totalAmount', 0):,.0f})"
            for p in projects[:10]
        ])
        
        return {
            "success": True,
            "response": f"📁 **Vidify HQ Projects** ({len(projects)} total):\n\n{project_list}",
            "data": {"projects": projects}
        }
    
    # ==================== TRANSACTION OPERATIONS ====================
    
    async def log_income(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log income transaction.
        
        Example prompts:
        - "Log income 50000 from Ahmad in Vidify"
        - "Received 10000 from ABC Company - add to Vidify"
        """
        amount = params.get("amount")
        client_name = params.get("client_name") or params.get("client") or params.get("from")
        description = params.get("description", "Client payment")
        
        if not amount:
            return {
                "success": False,
                "response": f"How much did you receive, {self.owner_name}?"
            }
        
        # Find client
        client_id = None
        if client_name:
            client = await self.firebase.find_client_by_name(client_name)
            if client:
                client_id = client.get("id")
        
        result = await self.firebase.add_transaction(
            transaction_type="income",
            amount=float(amount),
            description=description,
            category="Client Payment",
            client_id=client_id
        )
        
        if result.get("success"):
            from_text = f" from **{client_name}**" if client_name else ""
            return {
                "success": True,
                "response": f"💰 Logged income of **Rs {float(amount):,.0f}**{from_text} in Vidify, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't log income: {result.get('error')}"
            }
    
    async def log_expense(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log expense transaction.
        
        Example prompts:
        - "Add expense 5000 for equipment in Vidify"
        - "Log expense 2000 - software subscription"
        """
        amount = params.get("amount")
        category = params.get("category", "General")
        description = params.get("description", "Business expense")
        
        if not amount:
            return {
                "success": False,
                "response": f"How much was the expense, {self.owner_name}?"
            }
        
        result = await self.firebase.add_transaction(
            transaction_type="expense",
            amount=float(amount),
            description=description,
            category=category
        )
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"📝 Logged expense of **Rs {float(amount):,.0f}** ({category}) in Vidify, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't log expense: {result.get('error')}"
            }
    
    # ==================== TEAM OPERATIONS ====================
    
    async def add_team_member(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a team member.
        
        Example prompts:
        - "Add team member Hamza as Editor with salary 25000"
        - "Add Hamza to Vidify team"
        """
        name = params.get("name") or params.get("member_name")
        role = params.get("role", "Editor")
        salary = params.get("salary", 0)
        email = params.get("email", "")
        
        if not name:
            return {
                "success": False,
                "response": f"What's the team member's name, {self.owner_name}?"
            }
        
        result = await self.firebase.add_team_member(
            name=name,
            role=role,
            salary=float(salary) if salary else 0,
            email=email
        )
        
        if result.get("success"):
            salary_text = f" with salary Rs {float(salary):,.0f}" if salary else ""
            return {
                "success": True,
                "response": f"👤 Added **{name}** as {role}{salary_text} to Vidify team, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't add team member: {result.get('error')}"
            }
    
    async def pay_salary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pay salary to a team member.
        
        Example prompts:
        - "Pay Hamza salary 25000 in Vidify"
        - "Pay salary to Hamza - 30000"
        """
        member_name = params.get("name") or params.get("member_name") or params.get("to")
        amount = params.get("amount") or params.get("salary")
        
        if not member_name:
            return {
                "success": False,
                "response": f"Who should I pay, {self.owner_name}?"
            }
        
        if not amount:
            return {
                "success": False,
                "response": f"How much should I pay {member_name}, {self.owner_name}?"
            }
        
        # Find team member
        member = await self.firebase.find_team_member_by_name(member_name)
        
        if not member:
            return {
                "success": False,
                "response": f"Couldn't find team member '{member_name}' in Vidify, {self.owner_name}."
            }
        
        result = await self.firebase.pay_salary(
            member_id=member["id"],
            amount=float(amount)
        )
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"💵 Paid **Rs {float(amount):,.0f}** salary to **{member_name}** in Vidify, {self.owner_name}!",
                "data": result
            }
        else:
            return {
                "success": False,
                "response": f"❌ Couldn't pay salary: {result.get('error')}"
            }
    
    # ==================== STATS OPERATIONS ====================
    
    async def get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get dashboard statistics.
        
        Example prompts:
        - "Show Vidify dashboard"
        - "Vidify stats"
        - "How's Vidify doing?"
        """
        stats = await self.firebase.get_dashboard_stats()
        
        if not stats.get("success"):
            return {
                "success": False,
                "response": f"Couldn't get stats: {stats.get('error')}"
            }
        
        response = f"""📊 **Vidify HQ Dashboard Summary**

👥 **Clients:** {stats['total_clients']} total ({stats['active_clients']} active)
📁 **Projects:** {stats['total_projects']} total ({stats['active_projects']} in progress)
👤 **Team:** {stats['team_members']} members

💰 **Financials:**
• Total Income: Rs {stats['total_income']:,.0f}
• Total Expenses: Rs {stats['total_expenses']:,.0f}
• **Profit: Rs {stats['profit']:,.0f}**

Looking good, {self.owner_name}! 🚀"""
        
        return {
            "success": True,
            "response": response,
            "data": stats
        }


# Global instance
vidify_agent = VidifyDashboardAgent()

