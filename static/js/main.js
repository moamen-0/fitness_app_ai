/**
 * Main application script
 */
document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const exerciseList = document.getElementById('exercise-list');
    const exerciseInfo = document.getElementById('exercise-info');
    
    // Exercise descriptions
    const exerciseDescriptions = {
        'hummer': {
            name: 'Bicep Curl (Hammer) Exercise',
            description: 'An exercise to strengthen the front arm muscles (biceps) in a hammer grip style.',
            instructions: [
                'Stand straight holding weights beside your body',
                'Bend your elbows to lift the weight toward your shoulders while keeping your upper arms stationary',
                'Slowly lower the weight back to the starting position',
                'Continue to breathe normally during the exercise'
            ]
        },
        'front_raise': {
            name: 'Front Raise Exercise',
            description: 'An exercise to strengthen the front shoulder muscles.',
            instructions: [
                'Stand with weights in front of your thighs',
                'Lift your arms forward until they are parallel to the ground',
                'Slowly return the weight back to the starting position',
                'Keep your back straight throughout the exercise'
            ]
        },
        'squat': {
            name: 'Squat Exercise',
            description: 'A fundamental exercise to strengthen the leg and glute muscles.',
            instructions: [
                'Stand with your feet shoulder-width apart',
                'Lower your body as if you were sitting in a chair',
                'Keep your back straight and your knees above your feet',
                'Return to the standing position by pushing the ground with your heels'
            ]
        },
        'triceps': {
            name: 'Triceps Extension Exercise',
            description: 'An exercise to strengthen the rear arm muscles (triceps).',
            instructions: [
                'Stand with the weight overhead in both hands',
                'Bend your elbows to lower the weight behind your head',
                'Extend your arms to lift the weight back up',
                'Focus on moving only your elbows'
            ]
        },
        'lunges': {
            name: 'Lunges Exercise',
            description: 'An exercise to strengthen the leg and glute muscles with a focus on balance.',
            instructions: [
                'Stand with your feet facing forward',
                'Take a large step forward with one foot',
                'Lower your body until your front knee forms a 90-degree angle',
                'Push off the front foot to return to the starting position'
            ]
        },
        'shoulder_press': {
            name: 'Shoulder Press Exercise',
            description: 'An exercise to strengthen the shoulder muscles.',
            instructions: [
                'Stand or sit with weights at shoulder level',
                'Press the weights overhead until your arms are fully extended',
                'Slowly lower the weights back to shoulder level',
                'Repeat while keeping your back straight'
            ]
        },
        'plank': {
            name: 'Plank Exercise',
            description: 'An exercise to strengthen the core and back muscles and improve stability.',
            instructions: [
                'Lie on your stomach and lift your body supported by your forearms and toes',
                'Maintain a straight line from your head to your heels',
                'Tighten your core muscles and hold the position',
                'Try to hold the position for 30 seconds or more'
            ]
        },
        'side_lateral_raise': {
            name: 'Side Lateral Raise Exercise',
            description: 'An exercise to strengthen the lateral shoulder muscles.',
            instructions: [
                'Stand with weights at your sides',
                'Raise your arms out to the sides until they are parallel to the ground',
                'Slowly lower the weights back to the starting position',
                'Keep your elbows slightly straight during the exercise'
            ]
        },
        'triceps_kickback_side': {
            name: 'Triceps Kickback Exercise',
            description: 'An exercise to strengthen the rear arm muscles (triceps) from a side position.',
            instructions: [
                'Bend forward slightly, keeping your knees bent',
                'Pull your elbows back so they are high beside your body',
                'Extend your arms backward while keeping your elbows stationary',
                'Bend your arms slowly to return to the starting position'
            ]
        },
        'push_ups': {
            name: 'Push Up Exercise',
            description: 'A fundamental exercise to strengthen the chest, arms, and shoulder muscles.',
            instructions: [
                'Start in a prone position with your body supported by your hands and toes',
                'Lower your body by bending your elbows until your chest is close to the ground',
                'Push your body back up by extending your elbows',
                'Keep your body straight throughout the exercise'
            ]
        }
    };
    
    /**
     * Fetch available exercises from the server
     */
    async function fetchExercises() {
        try {
            const response = await fetch('/api/exercises');
            if (!response.ok) {
                throw new Error('Failed to fetch exercises');
            }
            
            const exercises = await response.json();
            renderExerciseList(exercises);
        } catch (error) {
            console.error('Error fetching exercises:', error);
            exerciseList.innerHTML = '<div class="alert alert-danger">Failed to load the exercise list</div>';
        }
    }
    
    /**
     * Render the list of exercises
     * @param {Array} exercises - List of available exercises
     */
    function renderExerciseList(exercises) {
        exerciseList.innerHTML = '';
        
        exercises.forEach(exercise => {
            const listItem = document.createElement('button');
            listItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            listItem.setAttribute('data-exercise-id', exercise.id);
            listItem.textContent = exercise.name;
            
            listItem.addEventListener('click', () => {
                // Remove active class from all items
                document.querySelectorAll('.list-group-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Add active class to selected item
                listItem.classList.add('active');
                
                // Start WebRTC connection for selected exercise
                window.rtcHandler.initConnection(exercise.id);
                
                // Show exercise info
                showExerciseInfo(exercise.id);
            });
            
            exerciseList.appendChild(listItem);
        });
    }
    
    /**
     * Show information about selected exercise
     * @param {string} exerciseId - ID of the selected exercise
     */
    function showExerciseInfo(exerciseId) {
        const exerciseData = exerciseDescriptions[exerciseId] || {
            name: 'Unknown',
            description: 'No description available',
            instructions: ['No instructions available']
        };
        
        let html = `
            <h5>${exerciseData.name}</h5>
            <p>${exerciseData.description}</p>
            <h6>Exercise Instructions:</h6>
            <ol>
        `;
        
        exerciseData.instructions.forEach(instruction => {
            html += `<li>${instruction}</li>`;
        });
        
        html += `
            </ol>
            <div class="alert alert-info mt-3">
                <i class="bi bi-info-circle"></i> Make sure to follow the instructions for the best results and to avoid injuries.
            </div>
        `;
        
        exerciseInfo.innerHTML = html;
    }
    
    




    // Initialize WebRTC handler
    window.rtcHandler.showNoExercise();
    
    // Fetch exercises when page loads
    fetchExercises();
});
