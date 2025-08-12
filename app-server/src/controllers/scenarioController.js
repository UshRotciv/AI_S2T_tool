const scenarioService = require('../services/scenarioService');
const axios = require('axios');

const handleSuccess = (res, data) => res.status(200).json({ success: true, data });
const handleError = (res, error, statusCode = 500) => {
    console.error(error); // Log the actual error
    res.status(statusCode).json({ success: false, error: error.message || 'An unexpected error occurred.' });
}

const getAllScenarios = async (req, res) => {
    try {
        const scenarios = await scenarioService.getAllScenarios();
        handleSuccess(res, scenarios);
    } catch (error) {
        handleError(res, error, 500);
    }
};

const getScenarioById = async (req, res) => {
    try {
        const { id } = req.params;
        const scenario = await scenarioService.getScenarioById(id);
        if (!scenario) {
            return res.status(404).json({ success: false, error: 'Scenario not found.' });
        }
        handleSuccess(res, scenario);
    } catch (error) {
        handleError(res, error, 500);
    }
};

const createScenario = async (req, res) => {
    try {
        // Assuming req.body contains the full scenario object including a unique id
        const newScenario = await scenarioService.createScenario(req.body);
        res.status(201).json({ success: true, data: newScenario });
    } catch (error) {
        handleError(res, error, 400); // 400 for bad request
    }
};

const updateScenario = async (req, res) => {
    try {
        const { id } = req.params;
        const updatedScenario = await scenarioService.updateScenario(id, req.body);
        if (!updatedScenario) {
            return res.status(404).json({ success: false, error: 'Scenario not found.' });
        }
        handleSuccess(res, updatedScenario);
    } catch (error) {
        handleError(res, error, 400);
    }
};

const deleteScenario = async (req, res) => {
    try {
        const { id } = req.params;
        const result = await scenarioService.deleteScenario(id);
        if (!result) {
            return res.status(404).json({ success: false, error: 'Scenario not found.' });
        }
        handleSuccess(res, { message: 'Scenario deleted successfully' });
    } catch (error) {
        handleError(res, error, 500);
    }
};

const askQuestion = async (req, res) => {
    try {
        const { question } = req.body;
        if (!question) {
            // Use new Error() for consistency in error objects
            return handleError(res, new Error('Question is required.'), 400);
        }
        // Forward the question to the Python AI service
        const aiServiceResponse = await axios.post('http://localhost:8001/api/ask', {
            question: question
        });

        const answer = aiServiceResponse.data.answer;
        handleSuccess(res, { answer });
    } catch (error) {
        handleError(res, error, 500);
    }
};

module.exports = {
    getAllScenarios,
    getScenarioById,
    createScenario,
    updateScenario,
    deleteScenario,
    askQuestion
};
