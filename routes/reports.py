"""
Admin Reports Routes
Handles rental history, revenue reports, and transaction logs
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request

from models.database import get_rentals_collection, get_scooters_collection, get_users_collection
from utils.responses import success_response, list_response, validation_error, server_error_response
from utils.auth import admin_required

logger = logging.getLogger(__name__)

# Create Blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')


@reports_bp.route('/rentals', methods=['GET'])
@admin_required
def get_rental_history():
    """
    Get all rental history with optional filters.
    Query params:
        - status: 'completed', 'active', or 'all' (default: 'all')
        - days: number of days to look back (default: 30)
        - user_id: filter by specific user
        - scooter_id: filter by specific scooter
    """
    logger.info(f"Admin request: GET /admin/reports/rentals - params: {dict(request.args)}")
    
    try:
        rentals = get_rentals_collection()
        users = get_users_collection()
        
        # Build query
        query = {}
        
        # Status filter
        status = request.args.get('status', 'all')
        if status != 'all':
            query['status'] = status
        
        # Date filter
        days = int(request.args.get('days', 30))
        if days > 0:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            query['start_time'] = {'$gte': cutoff_date}
        
        # User filter
        user_id = request.args.get('user_id')
        if user_id:
            query['user_id'] = user_id
        
        # Scooter filter
        scooter_id = request.args.get('scooter_id')
        if scooter_id:
            query['scooter_id'] = scooter_id
        
        # Fetch rentals
        rental_list = list(rentals.find(query, {'_id': 0}).sort('start_time', -1))
        
        # Enrich with user names
        user_cache = {}
        for rental in rental_list:
            uid = rental.get('user_id')
            if uid and uid not in user_cache:
                user = users.find_one({'id': uid}, {'name': 1, 'email': 1})
                user_cache[uid] = {
                    'name': user.get('name', 'Unknown') if user else 'Unknown',
                    'email': user.get('email', '') if user else ''
                }
            if uid:
                rental['user_name'] = user_cache[uid]['name']
                rental['user_email'] = user_cache[uid]['email']
        
        logger.info(f"Retrieved {len(rental_list)} rentals")
        return list_response(rental_list)
        
    except Exception as e:
        logger.error(f"Error fetching rental history: {e}", exc_info=True)
        return server_error_response("Failed to fetch rental history")


@reports_bp.route('/revenue', methods=['GET'])
@admin_required
def get_revenue_report():
    """
    Get revenue summary report.
    Query params:
        - period: 'today', 'week', 'month', 'year', 'all' (default: 'all')
    """
    logger.info(f"Admin request: GET /admin/reports/revenue - params: {dict(request.args)}")
    
    try:
        rentals = get_rentals_collection()
        
        now = datetime.utcnow()
        
        # Calculate date ranges
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        year_start = today_start.replace(month=1, day=1)
        
        # Helper to calculate revenue for a date range
        def calc_revenue(start_date=None):
            query = {'status': 'completed'}
            if start_date:
                query['end_time'] = {'$gte': start_date.isoformat()}
            
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': None,
                    'total_revenue': {'$sum': '$cost.total_cost'},
                    'total_rentals': {'$sum': 1},
                    'avg_rental': {'$avg': '$cost.total_cost'},
                    'total_unlock_fees': {'$sum': '$cost.unlock_fee'},
                    'total_rental_fees': {'$sum': '$cost.rental_fee'}
                }}
            ]
            
            result = list(rentals.aggregate(pipeline))
            if result:
                return {
                    'total_revenue': round(result[0].get('total_revenue', 0), 2),
                    'total_rentals': result[0].get('total_rentals', 0),
                    'avg_rental': round(result[0].get('avg_rental', 0), 2),
                    'total_unlock_fees': round(result[0].get('total_unlock_fees', 0), 2),
                    'total_rental_fees': round(result[0].get('total_rental_fees', 0), 2)
                }
            return {
                'total_revenue': 0,
                'total_rentals': 0,
                'avg_rental': 0,
                'total_unlock_fees': 0,
                'total_rental_fees': 0
            }
        
        # Calculate all periods
        report = {
            'generated_at': now.isoformat(),
            'today': calc_revenue(today_start),
            'this_week': calc_revenue(week_start),
            'this_month': calc_revenue(month_start),
            'this_year': calc_revenue(year_start),
            'all_time': calc_revenue(None),
            'date_ranges': {
                'today': today_start.strftime('%Y-%m-%d'),
                'week_start': week_start.strftime('%Y-%m-%d'),
                'month_start': month_start.strftime('%Y-%m-%d'),
                'year_start': year_start.strftime('%Y-%m-%d')
            }
        }
        
        # Get active rentals count
        active_count = rentals.count_documents({'status': 'active'})
        report['active_rentals'] = active_count
        
        # Get top performing scooters
        top_scooters_pipeline = [
            {'$match': {'status': 'completed'}},
            {'$group': {
                '_id': '$scooter_id',
                'total_revenue': {'$sum': '$cost.total_cost'},
                'rental_count': {'$sum': 1}
            }},
            {'$sort': {'total_revenue': -1}},
            {'$limit': 5}
        ]
        top_scooters = list(rentals.aggregate(top_scooters_pipeline))
        report['top_scooters'] = [
            {
                'scooter_id': s['_id'],
                'revenue': round(s['total_revenue'], 2),
                'rentals': s['rental_count']
            }
            for s in top_scooters
        ]
        
        logger.info(f"Revenue report generated: ${report['all_time']['total_revenue']:.2f} all-time")
        return success_response(report)
        
    except Exception as e:
        logger.error(f"Error generating revenue report: {e}", exc_info=True)
        return server_error_response("Failed to generate revenue report")


@reports_bp.route('/transactions', methods=['GET'])
@admin_required
def get_transaction_log():
    """
    Get transaction log for completed rentals.
    Query params:
        - days: number of days to look back (default: 7)
        - limit: max number of transactions (default: 100)
    """
    logger.info(f"Admin request: GET /admin/reports/transactions - params: {dict(request.args)}")
    
    try:
        rentals = get_rentals_collection()
        users = get_users_collection()
        
        days = int(request.args.get('days', 7))
        limit = min(int(request.args.get('limit', 100)), 500)  # Cap at 500
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Fetch completed rentals with transactions
        transactions = list(rentals.find(
            {
                'status': 'completed',
                'end_time': {'$gte': cutoff_date}
            },
            {'_id': 0}
        ).sort('end_time', -1).limit(limit))
        
        # Enrich with user info
        user_cache = {}
        transaction_log = []
        
        for rental in transactions:
            uid = rental.get('user_id')
            if uid and uid not in user_cache:
                user = users.find_one({'id': uid}, {'name': 1, 'email': 1})
                user_cache[uid] = user.get('name', 'Unknown') if user else 'Unknown'
            
            txn = rental.get('transaction', {})
            cost = rental.get('cost', {})
            
            transaction_log.append({
                'transaction_id': txn.get('transaction_id') or rental.get('transaction_id', 'N/A'),
                'authorization_code': txn.get('authorization_code', 'N/A'),
                'rental_id': rental.get('id'),
                'scooter_id': rental.get('scooter_id'),
                'user_name': user_cache.get(uid, 'Unknown'),
                'amount': cost.get('total_cost', 0),
                'unlock_fee': cost.get('unlock_fee', 0),
                'rental_fee': cost.get('rental_fee', 0),
                'pricing_tier': cost.get('pricing_tier', 'N/A'),
                'card_type': txn.get('card_type', 'N/A'),
                'card_last_four': txn.get('card_last_four', '****'),
                'status': txn.get('status', 'APPROVED'),
                'start_time': rental.get('start_time'),
                'end_time': rental.get('end_time'),
                'duration_minutes': cost.get('duration_minutes', 0),
                'is_simulation': txn.get('is_simulation', True)
            })
        
        # Calculate summary
        total_amount = sum(t['amount'] for t in transaction_log)
        
        logger.info(f"Retrieved {len(transaction_log)} transactions, total: ${total_amount:.2f}")
        
        return success_response({
            'transactions': transaction_log,
            'summary': {
                'count': len(transaction_log),
                'total_amount': round(total_amount, 2),
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching transaction log: {e}", exc_info=True)
        return server_error_response("Failed to fetch transaction log")


@reports_bp.route('/daily', methods=['GET'])
@admin_required  
def get_daily_breakdown():
    """
    Get daily revenue breakdown for charting.
    Query params:
        - days: number of days (default: 30)
    """
    logger.info(f"Admin request: GET /admin/reports/daily - params: {dict(request.args)}")
    
    try:
        rentals = get_rentals_collection()
        
        days = int(request.args.get('days', 30))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregate by day
        pipeline = [
            {
                '$match': {
                    'status': 'completed',
                    'end_time': {'$gte': cutoff_date.isoformat()}
                }
            },
            {
                '$addFields': {
                    'end_date': {'$substr': ['$end_time', 0, 10]}
                }
            },
            {
                '$group': {
                    '_id': '$end_date',
                    'revenue': {'$sum': '$cost.total_cost'},
                    'rentals': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        daily_data = list(rentals.aggregate(pipeline))
        
        # Fill in missing days with zeros
        result = []
        current = cutoff_date.date()
        end = datetime.utcnow().date()
        daily_map = {d['_id']: d for d in daily_data}
        
        while current <= end:
            date_str = current.isoformat()
            if date_str in daily_map:
                result.append({
                    'date': date_str,
                    'revenue': round(daily_map[date_str]['revenue'], 2),
                    'rentals': daily_map[date_str]['rentals']
                })
            else:
                result.append({
                    'date': date_str,
                    'revenue': 0,
                    'rentals': 0
                })
            current += timedelta(days=1)
        
        return success_response({
            'daily_breakdown': result,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error generating daily breakdown: {e}", exc_info=True)
        return server_error_response("Failed to generate daily breakdown")


