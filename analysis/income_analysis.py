import pandas as pd
import numpy as np
from datetime import timedelta

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.util import ngrams
nltk.download('stopwords')
nltk.download('punkt')

def analyze(transactions: pd.DataFrame) -> dict:
    """
    Analyze income transactions to identify salary payments
    """
    # Define result dictionary
    dict_statistics = {}

    filtered_transactions, last_transaction_date = pre_analysis(transactions)

    salary_dict= get_salary_analytics(filtered_transactions, last_transaction_date)
    dict_statistics.update(salary_dict)

    return dict_statistics


def pre_analysis(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-process transactions data and prepare necessary columns for analysis
    """
    # Convert date column to datetime
    transactions['date'] = pd.to_datetime(transactions['date'])

    # Make the date column timezone-naive to avoid warnings
    if transactions['date'].dt.tz is not None: transactions['date'] = transactions['date'].dt.tz_convert(None)
        
    # Filter for credit transactions
    credit_transactions = transactions[transactions['type'] == 'credit']

    # Sort transactions by date
    credit_transactions = credit_transactions.sort_values(by='date')

    # Extract the last transaction date
    last_transaction_date = credit_transactions['date'].max()

    # Filter transactions within a 1-year period from the last transaction date
    one_year_ago = last_transaction_date - timedelta(days=365)
    recent_transactions = credit_transactions[credit_transactions['date'] >= one_year_ago]

    # Group by amount and count occurrences
    amount_counts = recent_transactions.groupby('amount').size().reset_index(name='counts')

    # Sort by amount and counts and filter for frequent transactions that has happened at least twice
    frequent_amounts = amount_counts[amount_counts['counts'] >= 2].sort_values(by=['amount','counts'], ascending=False)

    # Get the top 10 amounts that have appeared most frequently
    top_frequent_amounts = frequent_amounts.head(10)
        
    # Filter transactions for these top frequent amounts
    filtered_transactions = recent_transactions[recent_transactions['amount'].isin(top_frequent_amounts['amount'])]

    # Reset dataframe index
    filtered_transactions = filtered_transactions.reset_index(drop=True)

    # Categorize payments
    filtered_transactions = categorize_payments(filtered_transactions)

    return filtered_transactions, last_transaction_date

def categorize_payments(transactions):
    # Tokenize and preprocess narrations
    stop_words = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    preprocessed_narrations = []
    for narration in transactions['narration']:
        tokens = word_tokenize(narration.lower())
        filtered_tokens = [stemmer.stem(token) for token in tokens if token not in stop_words]
        preprocessed_narrations.append(filtered_tokens)

    # Calculate pairwise similarity
    similarities = []
    for i in range(len(preprocessed_narrations)):
        row_similarities = []
        for j in range(len(preprocessed_narrations)):
            similarity = nltk.jaccard_distance(set(preprocessed_narrations[i]), set(preprocessed_narrations[j]))
            row_similarities.append(1 - similarity)  # Convert distance to similarity
        similarities.append(row_similarities)

    # Create a boolean matrix where similarity > 0.3
    boolean_matrix = np.array(similarities) > 0.3

    # Get the index of the first True value in each row
    categories = np.argmax(boolean_matrix, axis=1) + 1

    # Assign the categories to the DataFrame
    transactions['category'] = categories

    return transactions


def get_salary_analytics(transactions, last_transaction_date):
    salary_dict = {}
    # Prioritize recent transactions
    transactions['days_from_last'] = (last_transaction_date - transactions['date']).dt.days
    filtered_transactions = transactions.sort_values(by='days_from_last')

    # Group by month and select one transaction per month
    filtered_transactions['month'] = filtered_transactions['date'].dt.to_period('M')
    final_salary_transactions = filtered_transactions.drop_duplicates(subset=['month', 'amount']).copy()

    # Check if the payment occurred once in every month in the last 3 months for each payment category
    last_three_months = last_transaction_date.to_period('M') - 4
    recent_three_months = final_salary_transactions[final_salary_transactions['month'] >= last_three_months]

    # Filter for payments that are at least 20% of the maximum amount in the last 3 months (Remove lower boundary outliers)
    recent_three_months = recent_three_months[recent_three_months.amount >= recent_three_months.amount.max()*0.2]

    # Get payment categories that has occurred at least once in every month in the last 3 months
    categories_with_complete_months = recent_three_months.groupby('category').filter(lambda x: len(x['month'].unique()) >= 3)

    #Calculate salary mean and median income
    salary_mean = categories_with_complete_months['amount'].mean()
    salary_median = categories_with_complete_months['amount'].median()

    # Calculate median of all other income that has appeared in the last three months but with different categorie
    other_income_median = recent_three_months.amount.median()

    salary_dict['salary_mean'] = salary_mean
    salary_dict['median_income'] = salary_median
    salary_dict['other_income_median'] = other_income_median
    salary_dict['is_salary_earner'] = isSalaryEarner(salary_mean, other_income_median)

    # Get the best category for salary payments
    confidence_df = add_confidence_score(recent_three_months)
    max_category = confidence_df[confidence_df['weight'] == confidence_df['weight'].max()]['category'].values[0]
    salary_dict['number_of_salary_payments'] = get_number_of_salary_payments(final_salary_transactions, max_category)

    # Get the salary frequency
    salary_dict['salary_frequency'] = get_salary_frequency(filtered_transactions, max_category)

    # Get the last salary payment date
    salary_dict['last_salary_date'] = get_last_salary_date(final_salary_transactions)

    # Get the expected salary date
    salary_dict['expected_salary_date'] = expected_salary_date(final_salary_transactions)

    #Add confidence score
    salary_dict['confidence_score'] = confidence_df['weight'].mean()

    # Check if the user is a gig earner
    salary_dict['is_gig_earner'] = isGigEarner(final_salary_transactions, max_category)

    return salary_dict

def isSalaryEarner(salary_mean, median_income):
    if int(salary_mean) > 0.3*int(median_income):
        return True
    return False


def isGigEarner(filtered_transactions, max_category):
    filtered_transactions = filtered_transactions[filtered_transactions['category'] != max_category]

    last_six_months = filtered_transactions.to_period('M') - 6
    recent_three_months = filtered_transactions[filtered_transactions['month'] >= last_six_months]

    threshold = recent_three_months['amount'].mean()*0.4

    for month in recent_three_months['month'].unique():
        month_transactions = recent_three_months[recent_three_months['month'] == month]
        if month_transactions['amount'].max() > threshold:
            return True
    return False
     

def get_last_salary_date(transactions):
    return transactions.iloc[0]['date'].isoformat()
    

def get_salary_frequency(transactions, max_category):
    possible_salary_transactions = transactions[transactions['category'] == max_category]
    salary_counts = possible_salary_transactions['month'].value_counts()  
    max_count = salary_counts.max() if not salary_counts.empty else 0 

    if max_count == 1:
        return '1'
    elif max_count > 1:
        return '>1'
    return  None

def get_number_of_salary_payments(filtered_transactions, max_category):
    # Use the maximum category to filter for salary payments
    salary_payments = filtered_transactions[filtered_transactions['category'] == max_category]
    return salary_payments.shape[0]

def other_income_payment_frequency():
    pass

def expected_salary_date(transactions: pd.DataFrame) -> str:
    """
    Get the expected salary date based on the last salary payment date
    """

    # Get the average day of the last three months
    last_three_months = transactions['date'].nlargest(3)
    average_day = int(last_three_months.dt.day.mean())

    # Get the last salary payment date
    last_salary_date = transactions['date'].max()

    expected_salary_date = last_salary_date.replace(day=average_day, month=last_salary_date.month + 1)

    return expected_salary_date.isoformat()

def ngram_similarity(text1, text2, n=3):
    text1_grams = set(ngrams(text1.lower(), n))
    text2_grams = set(ngrams(text2.lower(), n))
    
    total_grams = len(text1_grams.union(text2_grams))
    common_grams = len(text1_grams.intersection(text2_grams))
    
    if total_grams == 0:
        return 0
    else:
        return common_grams / total_grams

def add_confidence_score(transactions: pd.DataFrame) -> pd.DataFrame:
    # Convert transaction dates to datetime objects
    transactions['date'] = pd.to_datetime(transactions['date'])

    # Group transactions by category and calculate count, start time, and value range
    category_stats = transactions.groupby('category')[['narration']].agg(
    count=('narration', 'count')
    ).join(
        transactions.groupby('category')[['date']].agg(
            start_time=('date', 'min')
        )
    ).join(
        transactions.groupby('category')[['amount']].agg(
            value_range=('amount', lambda x: x.max() - x.min())
        )
    ).reset_index()

    # Calculate the similarities within each category
    category_stats['similarities'] = category_stats['category'].apply(
        lambda x: transactions[transactions['category'] == x]['narration'].apply(
            lambda y: max([ngram_similarity(y, z) for z in transactions[transactions['category'] == x]['narration']])
        ).mean()
    )

    # Normalize the count, start_time, similarities, and value_range
    max_count = category_stats['count'].max()
    min_start_time = category_stats['start_time'].min()
    max_similarities = category_stats['similarities'].max()
    max_value_range = category_stats['value_range'].max()

    category_stats['count_norm'] = category_stats['count'] / max_count
    category_stats['start_time_norm'] = (category_stats['start_time'] - min_start_time) / (
        category_stats['start_time'].max() - min_start_time)
    category_stats['similarities_norm'] = category_stats['similarities'] / max_similarities
    category_stats['value_range_norm'] = category_stats['value_range'] / max_value_range

    # Calculate the weight as the average of the normalized features
    category_stats['weight'] = (
        category_stats['count_norm'] +
        (1 - category_stats['start_time_norm']) +
        category_stats['similarities_norm'] +
        category_stats['value_range_norm']
    ) / 4

    # Merge the weights back into the original DataFrame
    transactions = transactions.merge(category_stats[['category', 'weight']], on='category', how='left')

    return transactions
