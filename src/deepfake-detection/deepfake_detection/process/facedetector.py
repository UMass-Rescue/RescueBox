import cv2
import numpy as np


def area_of(left_top, right_bottom):
    """
    Compute the areas of rectangles given two corners.
    Args:
        left_top (N, 2): left top corner.
        right_bottom (N, 2): right bottom corner.
    Returns:
        area (N): return the area.
    """
    hw = np.clip(right_bottom - left_top, 0.0, None)
    return hw[..., 0] * hw[..., 1]


def iou_of(boxes0, boxes1, eps=1e-5):
    """
    Return intersection-over-union (Jaccard index) of boxes.
    Args:
        boxes0 (N, 4): ground truth boxes.
        boxes1 (N or 1, 4): predicted boxes.
        eps: a small number to avoid 0 as denominator.
    Returns:
        iou (N): IoU values.
    """
    lt = np.maximum(boxes0[..., :2], boxes1[..., :2])
    rb = np.minimum(boxes0[..., 2:], boxes1[..., 2:])
    overlap = area_of(lt, rb)
    a0 = area_of(boxes0[..., :2], boxes0[..., 2:])
    a1 = area_of(boxes1[..., :2], boxes1[..., 2:])
    return overlap / (a0 + a1 - overlap + eps)


def hard_nms(box_scores, iou_threshold, top_k=-1, candidate_size=200):
    """
    Perform hard non-maximum suppression to filter out overlapping boxes.
    Args:
        box_scores (N, 5): each row is [x1,y1,x2,y2,score]
        iou_threshold: IoU cutoff
        top_k: keep top_k highest-scoring boxes (<=0 = all)
        candidate_size: only consider this many top scores initially
    Returns:
        filtered box_scores[picked]
    """
    scores = box_scores[:, -1]
    boxes = box_scores[:, :-1]
    picked = []
    idxs = np.argsort(scores)
    idxs = idxs[-candidate_size:]
    while idxs.size > 0:
        cur = idxs[-1]
        picked.append(cur)
        if 0 < top_k == len(picked) or idxs.size == 1:
            break
        cur_box = boxes[cur]
        idxs = idxs[:-1]
        others = boxes[idxs]
        ious = iou_of(others, cur_box[np.newaxis, :])
        idxs = idxs[ious <= iou_threshold]
    return box_scores[picked]


def predict_face(
    width, height, confidences, boxes, prob_threshold, iou_threshold=0.5, top_k=-1
):
    """
    Turn raw ONNX-detector outputs into final bounding boxes.
    Args:
        width, height: original image dims
        confidences: (1,N,2) array
        boxes:       (1,N,4) array in normalized [0..1]
        prob_threshold: min probability for class=face
    Returns:
        (boxes_kx4, labels_k, probs_k)
    """
    conf = confidences[0]  # shape (N,2)
    bxs = boxes[0]  # shape (N,4)
    keep = []
    labels = []
    for cls in (1,):  # only face class
        ps = conf[:, cls]
        mask = ps > prob_threshold
        if not mask.any():
            continue
        sub_boxes = bxs[mask]
        sub_scores = ps[mask]
        stacked = np.concatenate([sub_boxes, sub_scores.reshape(-1, 1)], axis=1)
        final = hard_nms(stacked, iou_threshold, top_k)
        keep.append(final)
        labels += [cls] * final.shape[0]
    if not keep:
        return np.zeros((0, 4), dtype=int), np.array([], int), np.array([])
    all_boxes = np.vstack(keep)
    # scale to pixel coords
    all_boxes[:, [0, 2]] = (all_boxes[:, [0, 2]] * width).astype(int)
    all_boxes[:, [1, 3]] = (all_boxes[:, [1, 3]] * height).astype(int)
    return all_boxes[:, :4], np.array(labels), all_boxes[:, 4]


def faceDetector(orig_image, threshold=0.7, face_detector=None):
    """
    Full face detection pipeline using an ONNX session.
    Returns:
        boxes (K,4), labels (K,), probs (K,), center (tuple), already_headshot (bool)
    """
    if face_detector is None:
        raise ValueError("face_detector must be provided")
    h, w = orig_image.shape[:2]
    img = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (640, 480))
    mean = np.array([127, 127, 127])
    inp = ((img - mean) / 128.0).astype(np.float32)
    inp = np.transpose(inp, (2, 0, 1))[None, ...]
    name = face_detector.get_inputs()[0].name
    confs, bxs = face_detector.run(None, {name: inp})
    boxes, labels, probs = predict_face(w, h, confs, bxs, threshold)
    center = None
    headshot = False
    if boxes.shape[0] > 0:
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        i = areas.argmax()
        x1, y1, x2, y2 = boxes[i]
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        if areas[i] > 0.5 * w * h:
            headshot = True
    return boxes, labels, probs, center, headshot
