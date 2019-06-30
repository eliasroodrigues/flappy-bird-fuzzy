from itertools import cycle
import random
import sys

"""
    Trabalho de Inteligência Artificial

    Nome: Elias Eduardo Silva Rodrigues
    Matrícula: 0015920

    Para que o jogo funcione deve ser instalado os seguintes requisitos:
    'pygame'
    'numpy'
    'skfuzzy' ou 'scikit-fuzzy'
    'matplotlib'
    (Ver arquivo 'Pipfile'. Se necessário de mais explicações ver README do autor do jogo)

    Para rodar deve ser compilado o arquivo 'flappy.py' com o comando 'pipenv'.

    ```bash
    $ pipenv install
    $ pipenv run python flappy.py
    ```
"""


import pygame
from pygame.locals import *
import numpy as np
import skfuzzy as fuzz
import time
import matplotlib.pyplot as plt
from skfuzzy import control as ctrl

FPS = 30
SCREENWIDTH  = 288
SCREENHEIGHT = 512
PIPEGAPSIZE  = 100 # gap between upper and lower part of pipe
BASEY        = SCREENHEIGHT * 0.79
# image, sound and hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/redbird-upflap.png',
        'assets/sprites/redbird-midflap.png',
        'assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        'assets/sprites/yellowbird-upflap.png',
        'assets/sprites/yellowbird-midflap.png',
        'assets/sprites/yellowbird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

# list of pipes
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)


try:
    xrange
except NameError:
    xrange = range


def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption('Flappy Bird')

    # numbers sprites for score display
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    # game over sprite
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    # message sprite for welcome screen
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    # base (ground) sprite
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # sounds
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    SOUNDS['die']    = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit']    = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point']  = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing']   = pygame.mixer.Sound('assets/audio/wing' + soundExt)

    while True:
        # select random background sprites
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

        # select random player sprites
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        IMAGES['pipe'] = (
            pygame.transform.flip(
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), False, True),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hismask for pipes
        HITMASKS['pipe'] = (
            getHitmask(IMAGES['pipe'][0]),
            getHitmask(IMAGES['pipe'][1]),
        )

        # hitmask for player
        HITMASKS['player'] = (
            getHitmask(IMAGES['player'][0]),
            getHitmask(IMAGES['player'][1]),
            getHitmask(IMAGES['player'][2]),
        )

        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    # index of player to blit on screen
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # iterator used to change playerIndex after every 5th iteration
    loopIter = 0

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    # amount by which base can maximum shift to left
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # player shm for up-down motion on welcome screen
    playerShmVals = {'val': 0, 'dir': 1}

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                # make first flap sound and return values for mainGame
                SOUNDS['wing'].play()
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                }

        # adjust playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0,0))
        SCREEN.blit(IMAGES['player'][playerIndex],
                    (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        pygame.display.update()
        FPSCLOCK.tick(FPS)

################################################################################

"""
    Aqui realiza a entrada de dados para o Sistema de Lógica Fuzzy
"""
def fuzzyLogic(playerx, playery, lowerPipes, upperPipes, flapping):
    vFlappy = 0
    """ 
        Com esse código o pássaro consegue voar um pouco melhore, porém
        no meu computador ficou lento por conta dos cálculos devido ao loop
    """
    flapping.input['yBird'] = playery
    for pipe in lowerPipes:
        flapping.input['yPipeLw'] = pipe['y']
        flapping.input['xPipes']  = pipe['x']
        flapping.compute()
        vFlappy = flapping.output['bFlappy']    

    """
        Com esse código o pássaro consegue abanar porém fica com mais 
        desvios do que o código anterior. Em ambos os casos a colisão deve
        estar desligada.
    """
    # if (lowerPipes[0]['x'] <= playerx):
    #     flapping.input['yPipeLw'] = lowerPipes[1]['y']
    #     flapping.input['xPipes']  = lowerPipes[1]['x'] - 55
    #     flapping.compute()
    #     vFlappy = flapping.output['bFlappy']
    # elif (lowerPipes[1]['x'] <= playerx):
    #     flapping.input['yPipeLw'] = lowerPipes[0]['y']
    #     flapping.input['xPipes']  = lowerPipes[0]['x'] - 55
    #     flapping.compute()
    #     vFlappy = flapping.output['bFlappy']
    # else:
    #     flapping.input['yPipeLw'] = lowerPipes[0]['y']
    #     flapping.input['xPipes']  = lowerPipes[0]['x'] - 55
    #     flapping.compute()
    #     vFlappy = flapping.output['bFlappy']

    return vFlappy

################################################################################

def mainGame(movementInfo):
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo['playerIndexGen']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of upper pipes
    # gera dois pipes de uma vez
    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]

    # list of lowerpipe
    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    pipeVelX = -4

    # player velocity, max velocity, downward accleration, accleration on flap
    playerVelY    =  -9   # player's velocity along Y, default same as playerFlapped
    playerMaxVelY =  10   # max vel along Y, max descend speed
    playerMinVelY =  -8   # min vel along Y, max ascend speed
    playerAccY    =   1   # players downward accleration
    playerRot     =  45   # player's rotation
    playerVelRot  =   3   # angular speed
    playerRotThr  =  20   # rotation threshold
    playerFlapAcc =  -9   # players speed on flapping
    playerFlapped = False # True when player flaps

    ################################################################################

    """
        Sistema de Lógica Fuzzy para Flappy Bird

    """

    """ Variáveis Linguísticas """
    xPipes   = ctrl.Antecedent(np.arange(-60, 632, 1), 'xPipes')     # avalia a posição x dos pipes de baixo
    yPipeLw  = ctrl.Antecedent(np.arange(150, 350, 1), 'yPipeLw')    # avalia a posição y do pipe de baixo
    yBird    = ctrl.Antecedent(np.arange(0, 385, 1), 'yBird')        # avalia a posição y do pássaro
    bFlappy  = ctrl.Consequent(np.arange(0, 1, 0.01), 'bFlappy')     # avalia se o pássaro deve pular
    
    """ Avalia a posição y do pássaro de acordo com os valores 'alto', 'meio' e 'baixo' """
    yBird['alto']  = fuzz.trimf(yBird.universe, [0, 52, 105])       # o player pode estar no y alto
    yBird['meio']  = fuzz.trimf(yBird.universe, [100, 175, 250])    # o player pode estar no y medio
    yBird['baixo'] = fuzz.trimf(yBird.universe, [245, 312, 385])    # ou no y baixo
    
    """ Avalia a posição x do pipe de acordo com os valores 'longe', 'perto' e 'passou' """
    xPipes['passou'] = fuzz.trimf(xPipes.universe, [-60, 40, 45])   # o pipe pode ter passado a posição x do player
    xPipes['perto']  = fuzz.trimf(xPipes.universe, [40, 55, 80])    # o pipe pode estar bem próximo do player
    xPipes['longe']  = fuzz.trimf(xPipes.universe, [75, 252, 632])  # o pipe pode estar em um x bem maior que o do player

    """ Avalia a posição y do pipe de acordo com os valores 'alto' e 'baixo' """
    yPipeLw['baixo'] = fuzz.trimf(yPipeLw.universe, [150, 158, 175])    # o pipe de baixo pode estar com o y 'baixo'
    yPipeLw['alto']  = fuzz.trimf(yPipeLw.universe, [170, 190, 350])    # o pipe de baixo pode estar com o y 'alto'

    """ Avalia se o pássaro írá pular ou não pular """
    bFlappy['notFlappy'] = fuzz.trimf(bFlappy.universe, [0.0, 0.25, 0.5])   # valores menores que 0.5 o pássaro não pula
    bFlappy['yesFlappy'] = fuzz.trimf(bFlappy.universe, [0.4, 0.7, 1.0])    # valores maiores que 0.6 o pássaro pula

    """ Regras do sistema """
    rule1Not = ctrl.Rule(yBird['alto']  & xPipes['passou'] & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule2Not = ctrl.Rule(yBird['alto']  & xPipes['passou'] & yPipeLw['alto'],  bFlappy['notFlappy']) # ok
    rule3Not = ctrl.Rule(yBird['alto']  & xPipes['perto']  & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule4Not = ctrl.Rule(yBird['alto']  & xPipes['perto']  & yPipeLw['alto'],  bFlappy['notFlappy']) # ok
    rule5Not = ctrl.Rule(yBird['alto']  & xPipes['longe']  & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule6Not = ctrl.Rule(yBird['alto']  & xPipes['longe']  & yPipeLw['alto'],  bFlappy['notFlappy']) # ok
    rule7Not = ctrl.Rule(yBird['meio']  & xPipes['passou'] & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule8Not = ctrl.Rule(yBird['meio']  & xPipes['passou'] & yPipeLw['alto'],  bFlappy['notFlappy']) # ok
    rule9Not = ctrl.Rule(yBird['meio']  & xPipes['perto']  & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule10Yes = ctrl.Rule(yBird['meio']  & xPipes['perto']  & yPipeLw['alto'],  bFlappy['yesFlappy']) # ok
    rule11Yes = ctrl.Rule(yBird['meio']  & xPipes['longe']  & yPipeLw['baixo'], bFlappy['yesFlappy']) # ok
    rule12Yes = ctrl.Rule(yBird['meio']  & xPipes['longe']  & yPipeLw['alto'],  bFlappy['yesFlappy']) # ok
    rule13Not = ctrl.Rule(yBird['baixo'] & xPipes['passou'] & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule14Not = ctrl.Rule(yBird['baixo'] & xPipes['passou'] & yPipeLw['alto'],  bFlappy['notFlappy']) # ok
    rule15Not = ctrl.Rule(yBird['baixo'] & xPipes['perto']  & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule16Yes = ctrl.Rule(yBird['baixo'] & xPipes['perto']  & yPipeLw['alto'], bFlappy['yesFlappy']) # ok
    rule17Not = ctrl.Rule(yBird['baixo']  & xPipes['longe']  & yPipeLw['baixo'], bFlappy['notFlappy']) # ok
    rule18Yes = ctrl.Rule(yBird['baixo']  & xPipes['longe']  & yPipeLw['alto'],  bFlappy['yesFlappy']) # ok

    flapping_ctrl = ctrl.ControlSystem([
                    rule1Not, rule2Not, rule3Not, rule4Not, rule5Not, rule6Not, rule7Not, rule8Not, 
                    rule9Not, rule10Yes, rule11Yes, rule12Yes, rule13Not, rule14Not, rule15Not, 
                    rule16Yes, rule17Not, rule18Yes])
    flapping      = ctrl.ControlSystemSimulation(flapping_ctrl)

    """
        Fim das Regras

    """

    ################################################################################

    while True:
        ################################################################################

        """
            Entrada de dados para o sitema de lógica fuzzy

        """

        # vFlappy é a variável que irá receber o valor calculado no sistema.
        vFlappy = fuzzyLogic(playerx, playery, lowerPipes, upperPipes, flapping)
        print(vFlappy)

        """ 
            Execução do sistema de lógica fuzzy

        """

        for pipe in upperPipes:
            # A condição a seguir limita o pássaro de pular mais alto que o y do pipe de cima.
            # Essa condição foi criada devido ao fato de que o sistema calcula vários valores iguais
            # ocasionando vários pulos seguidos do pásaro, devido a isso optou-se por delimitar esse
            # valor.
            if (playery - 60 > (pipe['y'] + IMAGES['pipe'][0].get_height())):
                # Se o valor calculado for maior que esse mostrado, o pássaro deve realizar o salto.
                if (vFlappy >= 0.6986356794914398):
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    SOUNDS['wing'].play()
                elif (vFlappy > 0.4):
                    playerFlapped = False

        """
            Fim do Sistema de Lógica Fuzzy

        """

        ################################################################################

        # Aqui está a verificação de teclas. 'ESC' para fechar o jogo. 'ESPAÇO' ou 'SETA PARA CIMA' 
        # para saltar.
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if (event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP)):
                if playery > 2 * IMAGES['player'][0].get_height():
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    SOUNDS['wing'].play()

        """
            Aqui fica a verificação de colisão do pássaro com os canos. Optei por comentar
            pois o pássaro não consegue voar de forma exata entre os canos, ocasionando a
            perda do jogo.
        """

        # check for crash here
        # crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex},
        #                        upperPipes, lowerPipes)
        # if crashTest[0]:
        #     return {
        #         'y': playery,
        #         'groundCrash': crashTest[1],
        #         'basex': basex,
        #         'upperPipes': upperPipes,
        #         'lowerPipes': lowerPipes,
        #         'score': score,
        #         'playerVelY': playerVelY,
        #         'playerRot': playerRot
        #     }

        # check for score
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                SOUNDS['point'].play()

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        # rotate the player
        if playerRot > -90:
            playerRot -= playerVelRot

        # player's movement
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            playerRot = 45

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0,0))

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        # print score so player overlaps the score
        showScore(score)

        # Player rotation has a threshold
        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot
        
        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def showGameOverScreen(crashInfo):
    """crashes the player down ans shows gameover image"""
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7

    basex = crashInfo['basex']

    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']

    # play hit and die sounds
    SOUNDS['hit'].play()
    if not crashInfo['groundCrash']:
        SOUNDS['die'].play()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if playery + playerHeight >= BASEY - 1:
                    return

        # player y shift
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        # player velocity change
        if playerVelY < 15:
            playerVelY += playerAccY

        # rotate only when it's a pipe crash
        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0,0))

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        


        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
        SCREEN.blit(playerSurface, (playerx,playery))
        SCREEN.blit(IMAGES['gameover'], (50, 180))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
         playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    # BASEY = 404,48
    # BASEY * 0.6 - 100 = 142,688
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE)) # [0, 142,688]
    gapY += int(BASEY * 0.2) # [0, 142,688] + 80,896
    pipeHeight = IMAGES['pipe'][0].get_height() # 320
    pipeX = SCREENWIDTH + 10 # 298

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe [−239,104 , −96,416]
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE}, # lower pipes[180,896 , 323,584]
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0 # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASEY - 1:
        # print('Ground: ', player['y'] + player['h'])
        return [True, True]
    else:
        playerRect = pygame.Rect(player['x'], player['y'],
                      player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1+x][y1+y] and hitmask2[x2+x][y2+y]:
                return True
    return False

def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x,y))[3]))
    return mask

if __name__ == '__main__':
    main()
