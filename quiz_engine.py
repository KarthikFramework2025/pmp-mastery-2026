from database import get_questions, save_result

class QuizEngine:
    def __init__(self):
        self.questions = get_questions()
        self.current_index = 0

    def get_current_question(self):
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def submit_answer(self, selected_answer):
        question = self.questions[self.current_index]
        correct = 1 if selected_answer == question[6] else 0

        save_result(question[0], selected_answer, correct)
        self.current_index += 1

        return correct
