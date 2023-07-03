from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Expense
from website import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta


views = Blueprint('views', __name__)

def current_balance(user):
    expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()
    current_balance = user.bank_balance

    for expense in expenses:
        if expense.amount_type == 'debit':
            current_balance -= expense.amount
        elif expense.amount_type == 'credit':
            current_balance += expense.amount

    return current_balance


@views.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total_balance = current_balance(current_user)

    return render_template('transaction.html', expenses=expenses, total_balance=total_balance,current_user=current_user)

@views.route('/expense/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if expense:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    referring_page = request.referrer
    return redirect(referring_page)

@views.route('/add_expense', methods=['GET','POST'])
@login_required
def add_expense():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    expenses = expenses[:5] 
    total_balance = current_balance(current_user)
    return render_template('add_expense.html',expenses=expenses,total_balance=total_balance,current_user=current_user)

@views.route('/adding_expense', methods=['POST'])
@login_required
def adding_expense():
    if request.method == 'POST':
        amount = request.form.get('amount')
        amount_type = request.form.get('amount_type')
        description = request.form.get('description')
        date = request.form.get('date')
        input_date = datetime.strptime(date, '%Y-%m-%d').date()
        total_balance = current_balance(current_user)-float(amount)
        if float(amount)<=0:
            flash('Invalid Amount!','error')
        if total_balance<0:
            flash('Invalid Amount!','error')
        else:
            new_expense = Expense(amount=amount, description=description, date=input_date,amount_type=amount_type, user_id=current_user.id)
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
    return redirect(url_for('views.add_expense'))

def get_current_balance_data(day,user_id):
    current_balance_dates = []
    balances = []
    current_balance = 0

    for i in range(day-1, -1, -1):
        starting_date = (datetime.now().date() - timedelta(days=i)).strftime('%Y-%m-%d')

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date <= starting_date
        ).order_by(Expense.date).all()

        current_balance = current_user.bank_balance

        for expense in expenses:
            if expense.amount_type == 'debit':
                current_balance -= expense.amount
            elif expense.amount_type == 'credit':
                current_balance += expense.amount

        current_balance_dates.append(starting_date)
        balances.append(current_balance)

    return current_balance_dates, balances


def get_credit_data(day,user_id):
    credit_dates = []
    credits_list = []

    for i in range(day-1, -1, -1):
        starting_date = (datetime.now().date() - timedelta(days=i)).strftime('%Y-%m-%d')
        credit = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.date == starting_date,
            Expense.amount_type == 'credit'
        ).scalar()
        if credit is None:
            credit = 0

        credit_dates.append(starting_date)
        credits_list.append(credit)

    return credit_dates, credits_list


def get_debit_data(day,user_id):
    debit_dates = []
    debit_list = []

    for i in range(day-1, -1, -1):
        starting_date = (datetime.now().date() - timedelta(days=i)).strftime('%Y-%m-%d')
        debit = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.date == starting_date,
            Expense.amount_type == 'debit'
        ).scalar()
        if debit is None:
            debit = 0

        debit_dates.append(starting_date)
        debit_list.append(debit)

    return debit_dates, debit_list


@views.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id

    current_balance_dates, balances = get_current_balance_data(3,user_id)
    credit_dates, credits_list = get_credit_data(3,user_id)
    debit_dates, debit_list = get_debit_data(3,user_id)

    return render_template("dashboard.html",
                           current_balance_dates=current_balance_dates,
                           balances=balances,
                           credit_dates=credit_dates,
                           credits_list=credits_list,
                           debit_dates=debit_dates,
                           debit_list=debit_list,
                           current_user=current_user)


@views.route("/analytics", methods=['POST', 'GET'])
@login_required
def analytics():
    user_id = current_user.id
    day_range = int(request.form.get('day_range', 7))
   
    current_balance_dates, balances = get_current_balance_data(day_range, user_id)
    credit_dates, credits_list = get_credit_data(day_range, user_id)
    debit_dates, debit_list = get_debit_data(day_range, user_id)

    return render_template("analytics.html", current_balance_dates=current_balance_dates,
                           balances=balances,
                           credit_dates=credit_dates,
                           credits_list=credits_list,
                           debit_dates=debit_dates,
                           debit_list=debit_list,
                           current_user=current_user)
