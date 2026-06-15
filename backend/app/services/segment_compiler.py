from sqlalchemy import func, select, and_, or_, not_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.crm import Customer, Order
from app.schemas.crm import SegmentDefinition, ConditionNode

def compile_segment(db: Session, definition: SegmentDefinition):

    query = db.query(Customer)
    

    agg_sub = db.query(
        Order.customer_id,
        func.sum(Order.amount).label("total_spend"),
        func.count(Order.id).label("order_count"),
        func.max(Order.created_at).label("last_order_date")
    ).filter(Order.status == "completed").group_by(Order.customer_id).subquery()
    


    query = query.outerjoin(agg_sub, Customer.id == agg_sub.c.customer_id)
    
    clauses = []
    
    for condition in definition.conditions:
        field = condition.field
        op = condition.operator
        val = condition.value
        
        clause = None
        

        if field == "customer.total_spend":
            col = func.coalesce(agg_sub.c.total_spend, 0)
            clause = build_comparison_clause(col, op, val)
        elif field == "customer.order_count":
            col = func.coalesce(agg_sub.c.order_count, 0)
            clause = build_comparison_clause(col, op, val)
        elif field == "customer.last_order_date":

            parsed_val = parse_date_value(val)
            col = agg_sub.c.last_order_date
            clause = build_comparison_clause(col, op, parsed_val)
            

        elif field.startswith("customer.properties."):
            prop_key = field.replace("customer.properties.", "")
            col = Customer.properties[prop_key].astext
            clause = build_comparison_clause(col, op, val)
            

        elif field == "customer.email":
            clause = build_comparison_clause(Customer.email, op, val)
        elif field == "customer.first_name":
            clause = build_comparison_clause(Customer.first_name, op, val)
        elif field == "customer.last_name":
            clause = build_comparison_clause(Customer.last_name, op, val)
        elif field == "customer.phone":
            clause = build_comparison_clause(Customer.phone, op, val)
            

        elif field == "order.category":


            exists_clause = db.query(Order.id).filter(
                Order.customer_id == Customer.id,
                Order.properties["category"].astext == str(val),
                Order.status == "completed"
            ).exists()
            if op in ["equals", "is"]:
                clause = exists_clause
            elif op in ["not_equals", "is_not"]:
                clause = not_(exists_clause)
                
        if clause is not None:
            clauses.append(clause)
            

    if not clauses:
        return query
        
    if definition.conjunction.upper() == "OR":
        query = query.filter(or_(*clauses))
    else:
        query = query.filter(and_(*clauses))
        
    return query

def build_comparison_clause(column, operator: str, value):
    op = operator.lower()
    if op in ["equals", "eq", "is"]:
        return column == value
    elif op in ["not_equals", "neq", "is_not"]:
        return column != value
    elif op in ["greater_than", "gt"]:
        return column > value
    elif op in ["less_than", "lt"]:
        return column < value
    elif op in ["greater_than_or_equal", "gte"]:
        return column >= value
    elif op in ["less_than_or_equal", "lte"]:
        return column <= value
    elif op in ["contains", "like"]:
        return column.ilike(f"%{value}%")
    elif op in ["in"]:
        return column.in_(value)
    return None

def parse_date_value(val):
    if isinstance(val, (int, float)):

        return datetime.utcnow() - timedelta(days=val)
    elif isinstance(val, str):
        if val.endswith("_days_ago"):
            try:
                days = int(val.split("_")[0])
                return datetime.utcnow() - timedelta(days=days)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            pass
    return val
