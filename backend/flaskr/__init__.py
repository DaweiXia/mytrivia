import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resources={
    r"/questions/*": {"origins": "*"},
    r"/categories/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization")
    response.headers.add('Access-Control-Allow-Credentials', "true")
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()

    if len(categories) == 0:
      abort(404)

    formated_categories = {category.id: category.type for category in categories}
    return jsonify({
      'success': True,
      'categories': formated_categories
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions', methods=['GET', 'POST'])
  def get_questions():
    if request.method == 'GET':
      page = request.args.get('page', 1, type=int)
      start = (page - 1) * QUESTIONS_PER_PAGE
      end = start + QUESTIONS_PER_PAGE
      questions = Question.query.all()
      categories = Category.query.all()

      if (len(questions) == 0 or len(categories) == 0 or
      len(questions) < start):
        abort(404)

      formated_questions = [question.format() for question in questions]
      formated_categories = {category.id: category.type for category in categories}

      return jsonify({
        'success': True,
        'questions': formated_questions[start:end],
        'total_questions': len(formated_questions),
        'categories': formated_categories,
        'current_category': None
      })
    elif request.method == 'POST':
      data = request.json
      if 'searchTerm' in data:
        return get_questions_by_search_term(data['searchTerm'])
      else:
        return create_question(data)


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      return jsonify({'success': True})
    except:
      db.session.rollback()
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  def create_question(data):
    try:
      question = Question(question=data['question'], answer=data['answer'],
      category=data['category'], difficulty=data['difficulty'])
      question.insert()
      return jsonify({'success': True})
    except:
      db.session.rollback()
      abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  def get_questions_by_search_term(search_term):
    if search_term:
      questions = Question.query.filter(Question.question.contains(search_term)).all()
      
      if questions:     
        formated_questions = [question.format() for question in questions]
        return jsonify({
          'success': True,
          'questions': formated_questions,
          'total_questions': len(formated_questions),
          'current_category': None
        })
      else:
        abort(404)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    questions = Question.query.filter(Question.category == category_id).all()

    if questions:    
      formated_questions = [question.format() for question in questions]
      return jsonify({
        'success': True,
        'questions': formated_questions,
        'total_questions': len(formated_questions),
        'current_category': category_id
      })
    else:
      abort(404)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_next_question():
    previous_questions = request.json['previous_questions']
    quiz_category = request.json['quiz_category']
    if quiz_category['id'] == 0:
      questions = Question.query.all()
    else:
      questions = Question.query.filter(Question.category == quiz_category['id']).all()
    
    if questions:
      if len(previous_questions) == len(questions):
        question = None
        return jsonify({
          'success': True,
          'question': question
        })
      else:
        question = random.choice(questions)
        while question.id in previous_questions:
          question = random.choice(questions)
        return jsonify({
          'success': True,
          'question': question.format()
        })
    else:
      abort(404)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'Resource Not Found'
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'Unprocessable'
    }), 422
  
  
  return app

    