import argparse
import glob
import os
from typing import Tuple, List

import pygame
from pygame import Surface
import json


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900

NORMAL_DELAY = 20
SPEEDUP_DELAY = 5
HALT_DELAY = 100


def load_target_image(path_to_images: List[str], index: int, screen_width: int) -> Tuple[Surface, Tuple[int, int], float, str]:
    path_to_image = path_to_images[index]
    pygame.display.set_caption(path_to_image)
    image = pygame.image.load(path_to_image)
    width, height = image.get_width(), image.get_height()
    scale = screen_width / width
    width, height = int(width * scale), int(height * scale)
    image = pygame.transform.scale(image, (width, height))
    return image, (width, height), scale, path_to_image


def image_path_to_image_id(path_to_image):
    return path_to_image.split('/')[-1].split('.')[0]


def run(path_to_images_dir: str, path_to_annotation_json: str):
    pygame.init()
    done = False

    screen_width, screen_height = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))

    sight_image: Surface = pygame.image.load(os.path.join('asset', 'imgs', 'sight.png'))
    sight_width, sight_height = 50, 50
    sight_image = pygame.transform.scale(sight_image, (sight_width, sight_height))

    lock_image: Surface = pygame.image.load(os.path.join('asset', 'imgs', 'lock.png'))
    lock_width, lock_height = 10, 10
    lock_image = pygame.transform.scale(lock_image, (lock_width, lock_height))

    path_to_images = sorted(glob.glob(os.path.join(path_to_images_dir, '*.jpg')))
    image_id_to_annotation_dict = {image_path_to_image_id(it): {'x': None, 'y': None} for it in path_to_images}

    os.makedirs(os.path.dirname(path_to_annotation_json), exist_ok=True)

    if os.path.exists(path_to_annotation_json):
        print(f'{path_to_annotation_json} already exists, loading annotation...')
        with open(path_to_annotation_json, 'r') as f:
            image_id_to_annotation_dict = json.load(f)

    target_index = 0
    target_image, (target_width, target_height), scale, path_to_image = load_target_image(path_to_images, target_index, screen_width)
    target_x, target_y = 0, 0

    image_id = image_path_to_image_id(path_to_image)
    sight_cx = (image_id_to_annotation_dict[image_id]['x'] * scale) if image_id_to_annotation_dict[image_id]['x'] is not None else None
    sight_cy = (image_id_to_annotation_dict[image_id]['y'] * scale) if image_id_to_annotation_dict[image_id]['y'] is not None else None

    locks_sight = False

    while True:
        if done:
            break

        delay = NORMAL_DELAY

        screen.fill((255, 255, 255))
        screen.blit(target_image, (target_x, target_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sight_cx, sight_cy = event.pos

        directions = [0, 0]  # [x, y]
        offsets = [0, 0]  # [dx, dy]
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE] or keys[pygame.K_BACKSPACE]:
            target_offset = 0
            delay = HALT_DELAY

            if keys[pygame.K_SPACE]:
                target_offset += 1
            elif keys[pygame.K_BACKSPACE]:
                target_offset -= 1

            if keys[pygame.K_x]:
                delay = SPEEDUP_DELAY

            image_id = image_path_to_image_id(path_to_image)
            image_id_to_annotation_dict[image_id]['x'] = (sight_cx / scale) if sight_cx is not None else None
            image_id_to_annotation_dict[image_id]['y'] = (sight_cy / scale) if sight_cy is not None else None

            target_index += target_offset
            target_index %= len(path_to_images)
            target_image, (target_width, target_height), scale, path_to_image = load_target_image(path_to_images, target_index, screen_width)

            if not locks_sight:
                image_id = image_path_to_image_id(path_to_image)
                sight_cx = (image_id_to_annotation_dict[image_id]['x'] * scale) if image_id_to_annotation_dict[image_id]['x'] is not None else None
                sight_cy = (image_id_to_annotation_dict[image_id]['y'] * scale) if image_id_to_annotation_dict[image_id]['y'] is not None else None

        if keys[pygame.K_LEFT]:
            directions[0] = 1
            offsets[0] -= 2
        elif keys[pygame.K_RIGHT]:
            directions[0] = 1
            offsets[0] += 2
        if keys[pygame.K_UP]:
            directions[1] = 1
            offsets[1] -= 2
        elif keys[pygame.K_DOWN]:
            directions[1] = 1
            offsets[1] += 2

        if keys[pygame.K_x]:
            offsets = [it * 10 for it in offsets]

        if sight_cx is not None and sight_cy is not None:
            sight_cx += offsets[0] * directions[0]
            sight_cy += offsets[1] * directions[1]

            if sight_cx < 0:
                sight_cx = target_width - 1
            elif sight_cx >= target_width:
                sight_cx = 0

            if sight_cy < 0:
                sight_cy = target_height - 1
            elif sight_cy >= target_height:
                sight_cy = 0

            screen.blit(sight_image, (sight_cx - sight_width // 2, sight_cy - sight_height // 2))

            if locks_sight:
                screen.blit(lock_image,
                            (sight_cx + sight_width // 2 - lock_width, sight_cy + sight_height // 2 - lock_height))

        if keys[pygame.K_ESCAPE]:
            sight_cx, sight_cy = None, None

        if keys[pygame.K_s]:
            print('saving annotation...')
            with open(path_to_annotation_json, 'w') as f:
                json.dump(image_id_to_annotation_dict, f)
            print('annotation saved to {:s} (total {:d} keys)'.format(path_to_annotation_json, len(image_id_to_annotation_dict)))
            delay = HALT_DELAY

        if keys[pygame.K_l]:
            locks_sight = not locks_sight
            delay = HALT_DELAY

        pygame.display.update()
        pygame.time.delay(delay)

    pygame.quit()


if __name__ == '__main__':
    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('images_dir', type=str, help='path to images directory')
        parser.add_argument('annotation_json', type=str, help='path to annotation json')
        args = parser.parse_args()

        path_to_images_dir = args.images_dir
        path_to_annotation_json = args.annotation_json

        run(path_to_images_dir, path_to_annotation_json)

    main()
